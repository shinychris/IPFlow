"""认证 API 路由.

提供用户认证相关的端点：
- POST /auth/register - 用户注册
- POST /auth/login - 用户登录
- POST /auth/logout - 用户登出（预留）
- POST /auth/refresh - 刷新令牌
- GET /auth/me - 获取当前用户
"""

from typing import Annotated, Any, Optional
from uuid import uuid4
import logging

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.core.exceptions import (
    AuthenticationException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from ipflow.core.rate_limit import limiter
from ipflow.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)
from ipflow.db import get_db
from ipflow.models.user import User, UserRole, UserStatus, UserResponse
from ipflow.models import Organization, OrganizationMember

logger = logging.getLogger(__name__)

router = APIRouter(tags=["认证"])
security = HTTPBearer(auto_error=False)


# =============================================================================
# 请求/响应模型
# =============================================================================


class UserRegisterRequest(BaseModel):
    """用户注册请求模型."""
    
    email: EmailStr = Field(..., description="邮箱地址", max_length=255)
    username: str = Field(..., description="用户名", min_length=3, max_length=50)
    password: SecretStr = Field(..., description="密码", min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, description="显示名称", max_length=100)
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式."""
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        if not v[0].isalpha():
            raise ValueError("用户名必须以字母开头")
        return v.lower()
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: SecretStr) -> SecretStr:
        """验证密码强度."""
        password = v.get_secret_value()
        if len(password) < 8:
            raise ValueError("密码长度至少为 8 位")
        # 可选：添加更复杂的密码强度验证
        return v


class UserLoginRequest(BaseModel):
    """用户登录请求模型."""
    
    username: str = Field(..., description="用户名或邮箱", min_length=1, max_length=255)
    password: SecretStr = Field(..., description="密码", min_length=1)


class TokenRefreshRequest(BaseModel):
    """令牌刷新请求模型."""
    
    refresh_token: str = Field(..., description="刷新令牌", min_length=1)


class UserProfileUpdateRequest(BaseModel):
    """用户资料更新请求模型."""

    display_name: Optional[str] = Field(
        None, description="显示名称（昵称）", max_length=100
    )
    email: Optional[EmailStr] = Field(None, description="邮箱地址", max_length=255)


class TokenResponse(BaseModel):
    """令牌响应模型（OAuth2 标准格式）."""
    
    access_token: str = Field(..., description="访问令牌")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="访问令牌过期时间（秒）")


class RegisterResponseData(BaseModel):
    """注册响应数据模型."""
    
    id: str
    email: str
    username: str
    display_name: Optional[str] = None
    access_token: str
    token_type: str = "bearer"


class LoginResponseData(TokenResponse):
    """登录响应数据模型."""
    
    user_id: str
    username: str


class RefreshResponseData(BaseModel):
    """刷新令牌响应数据模型."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SuccessResponse(BaseModel):
    """统一成功响应格式."""
    
    success: bool = True
    code: str = "SUCCESS"
    message: str = "操作成功"
    data: Optional[Any] = None


# =============================================================================
# 数据库操作辅助函数
# =============================================================================


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """根据邮箱获取用户.
    
    Args:
        db: 数据库会话
        email: 邮箱地址
        
    Returns:
        用户对象或 None
    """
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """根据用户名获取用户.
    
    Args:
        db: 数据库会话
        username: 用户名
        
    Returns:
        用户对象或 None
    """
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.username == username.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """根据 ID 获取用户.
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        
    Returns:
        用户对象或 None
    """
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str,
    display_name: Optional[str] = None,
) -> User:
    """创建新用户.
    
    Args:
        db: 数据库会话
        email: 邮箱地址
        username: 用户名
        password: 明文密码（将被哈希）
        display_name: 显示名称
        
    Returns:
        创建的用户对象
    """
    user = User(
        email=email.lower(),
        username=username.lower(),
        hashed_password=get_password_hash(password),
        display_name=display_name,
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,

    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# =============================================================================
# 依赖注入
# =============================================================================


async def get_current_user(
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前认证用户.
    
    Args:
        authorization: Authorization 请求头
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        AuthenticationException: 认证失败
        NotFoundException: 用户不存在
    """
    if not authorization:
        raise AuthenticationException(message="缺少认证令牌")
    
    # 解析 Bearer Token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationException(message="无效的认证头格式")
    
    token = parts[1]
    
    # 验证令牌
    try:
        user_id = verify_access_token(token)
    except ValueError as e:
        raise AuthenticationException(message=f"无效的令牌: {str(e)}") from e
    
    # 获取用户
    user = await get_user_by_id(db, user_id)
    if not user:
        raise NotFoundException(resource="user", resource_id=user_id)
    
    # 检查用户是否激活
    if user.status != UserStatus.ACTIVE:
        raise AuthenticationException(message="用户账号已被禁用")
    
    return user


# =============================================================================
# API 端点
# =============================================================================


@router.post(
    "/auth/register",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="注册新用户账号，返回用户信息和访问令牌。",
)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """用户注册.
    
    Args:
        request: 注册请求数据
        db: 数据库会话
        
    Returns:
        包含用户信息和令牌的成功响应
        
    Raises:
        ValidationException: 邮箱或用户名已存在
    """
    # 检查邮箱是否已存在（与现有资源冲突 → 409 Conflict，而非 422 校验错误）
    existing_email = await get_user_by_email(db, request.email)
    if existing_email:
        raise ConflictException(
            message="该邮箱已被注册",
            field_errors=[{"field": "email", "message": "邮箱已被使用"}],
        )

    # 检查用户名是否已存在
    existing_username = await get_user_by_username(db, request.username)
    if existing_username:
        raise ConflictException(
            message="该用户名已被使用",
            field_errors=[{"field": "username", "message": "用户名已被占用"}],
        )
    
    # 创建用户
    user = await create_user(
        db=db,
        email=request.email,
        username=request.username,
        password=request.password.get_secret_value(),
        display_name=request.display_name,
    )

    # 为新用户创建个人组织（默认租户上下文，使订阅/配额等组织级能力开箱可用）
    # 出错时仅记录日志并继续，保证注册主流程永不因此失败
    try:
        personal_org = Organization(
            name=f"{user.display_name or user.username} 的个人空间",
            slug=f"personal-{user.username}-{uuid4().hex[:6]}",
            business_type="individual",
        )
        db.add(personal_org)
        await db.flush()  # 获取 personal_org.id

        member = OrganizationMember(
            organization_id=personal_org.id,
            user_id=user.id,
            role=UserRole.ADMIN,
        )
        db.add(member)
        await db.commit()
    except Exception as e:  # noqa: BLE001
        logger.warning("为用户 %s 创建个人组织失败，已跳过：%s", getattr(user, "id", None), e)

    # 生成访问令牌
    access_token = create_access_token(str(user.id))

    # 发送邮箱验证邮件（失败不阻断注册主流程）
    try:
        from ipflow.core.action_token import create_action_token, PURPOSE_EMAIL_VERIFICATION
        from ipflow.services.email_service import send_email_verification

        verify_token = create_action_token(str(user.id), PURPOSE_EMAIL_VERIFICATION)
        verify_url = _build_frontend_url(f"auth/verify-email?token={verify_token}")
        await send_email_verification(user.email, user.username, verify_url)
    except Exception as e:  # noqa: BLE001
        logger.warning("发送注册验证邮件失败（to=%s）：%s", user.email, e)

    return SuccessResponse(
        code="SUCCESS",
        message="注册成功",
        data=RegisterResponseData(
            id=str(user.id),
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            access_token=access_token,
            token_type="bearer",
        ),
    )


@router.post(
    "/auth/login",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="用户登录",
    description="使用用户名和密码登录，返回访问令牌和刷新令牌。",
)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """用户登录.
    
    Args:
        request: 登录请求数据
        db: 数据库会话
        
    Returns:
        包含令牌的成功响应
        
    Raises:
        AuthenticationException: 认证失败
    """
    # 查找用户（支持用户名或邮箱登录）
    user = await get_user_by_username(db, request.username)
    if not user and "@" in request.username:
        user = await get_user_by_email(db, request.username)
    
    # 验证用户存在
    if not user:
        raise AuthenticationException(message="用户名或密码错误")
    
    # 验证用户激活状态
    if user.status != UserStatus.ACTIVE:
        raise AuthenticationException(message="用户账号已被禁用")
    
    # 验证密码
    if not verify_password(request.password.get_secret_value(), user.hashed_password):
        raise AuthenticationException(message="用户名或密码错误")
    
    # 生成令牌
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    # 更新最后登录时间
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # 获取配置以计算过期时间
    from ipflow.config import get_settings
    settings = get_settings()
    
    return SuccessResponse(
        code="SUCCESS",
        message="登录成功",
        data=LoginResponseData(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            username=user.username,
        ),
    )


@router.post(
    "/auth/logout",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="用户登出",
    description="用户登出，吊销当前访问令牌。",
)
async def logout(
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    """用户登出.

    将当前访问令牌加入黑名单（令牌吊销）。

    黑名单服务优先使用 Redis（多实例共享），Redis 不可用时降级到进程内集合。
    客户端在收到响应后仍应删除本地存储的令牌。

    Args:
        authorization: Authorization 请求头（Bearer 令牌）
        current_user: 当前认证用户

    Returns:
        成功响应
    """
    from ipflow.core.token_blacklist import revoke_token
    from ipflow.core.security import decode_access_token

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        # 注意：decode_access_token 会检查黑名单，此处用于读取 jti/exp；
        # 由于当前令牌尚未吊销，payload 应非空。
        if payload:
            revoke_token(payload.get("jti", ""), payload.get("exp"))

    return SuccessResponse(
        code="SUCCESS",
        message="登出成功",
        data=None,
    )


@router.post(
    "/auth/refresh",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌。",
)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """刷新访问令牌.
    
    Args:
        request: 刷新令牌请求
        db: 数据库会话
        
    Returns:
        包含新访问令牌的成功响应
        
    Raises:
        AuthenticationException: 令牌无效或过期
    """
    # 验证刷新令牌
    try:
        user_id = verify_refresh_token(request.refresh_token)
    except ValueError as e:
        raise AuthenticationException(message=f"无效的刷新令牌: {str(e)}") from e
    
    # 验证用户存在
    user = await get_user_by_id(db, user_id)
    if not user:
        raise AuthenticationException(message="用户不存在")
    
    # 验证用户激活状态
    if user.status != UserStatus.ACTIVE:
        raise AuthenticationException(message="用户账号已被禁用")
    
    # 生成新的访问令牌
    access_token = create_access_token(user_id)
    
    # 获取配置以计算过期时间
    from ipflow.config import get_settings
    settings = get_settings()
    
    return SuccessResponse(
        code="SUCCESS",
        message="令牌刷新成功",
        data=RefreshResponseData(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


@router.get(
    "/auth/me",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="获取当前用户",
    description="获取当前认证用户的详细信息。",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse:
    """获取当前用户信息.
    
    Args:
        current_user: 当前认证用户
        
    Returns:
        包含用户详细信息的成功响应
    """
    return SuccessResponse(
        code="SUCCESS",
        message="获取用户信息成功",
        data=UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            username=current_user.username,
            display_name=current_user.display_name,
            role=current_user.role,
            status=current_user.status,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            last_login_at=current_user.last_login_at,
        ),
    )


@router.put(
    "/auth/me",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="更新当前用户资料",
    description="更新当前认证用户的昵称等个人资料。",
)
async def update_me(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """更新当前用户资料.

    Args:
        request: 待更新的资料字段（均为可选）
        current_user: 当前认证用户
        db: 数据库会话

    Returns:
        更新后的用户信息

    Raises:
        ConflictException: 邮箱已被其他用户占用
    """
    if request.display_name is not None:
        current_user.display_name = request.display_name.strip() or None

    if request.email is not None:
        new_email = request.email.lower()
        if new_email != current_user.email:
            existing = await get_user_by_email(db, new_email)
            if existing and str(existing.id) != str(current_user.id):
                raise ConflictException(
                    message="该邮箱已被注册",
                    field_errors=[{"field": "email", "message": "邮箱已被使用"}],
                )
            current_user.email = new_email

    await db.commit()
    await db.refresh(current_user)

    return SuccessResponse(
        code="SUCCESS",
        message="更新成功",
        data=UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            username=current_user.username,
            display_name=current_user.display_name,
            role=current_user.role,
            status=current_user.status,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
            last_login_at=current_user.last_login_at,
        ),
    )


# ==================== 邮箱验证与密码重置 ====================
# 这两组端点基于带用途（purpose）的短时效 JWT 令牌（见 core/action_token.py），
# 通过邮件链接回传，解决「注册即用无法防机器号」与「忘记密码无法自助恢复」两大 P1 缺口。


class ResendVerificationRequest(BaseModel):
    """重新发送验证邮件请求."""
    model_config = {"populate_by_name": True}

    email: EmailStr = Field(description="注册邮箱")


class VerifyEmailRequest(BaseModel):
    """邮箱验证请求（前端从邮件链接提取 token 后调用）."""
    model_config = {"populate_by_name": True}

    token: str = Field(description="邮箱验证令牌")


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求."""
    model_config = {"populate_by_name": True}

    email: EmailStr = Field(description="注册邮箱")


class ResetPasswordRequest(BaseModel):
    """重置密码请求."""
    model_config = {"populate_by_name": True}

    token: str = Field(description="密码重置令牌")
    new_password: SecretStr = Field(description="新密码（需符合强度要求）")

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: SecretStr) -> SecretStr:
        """复用注册时的密码强度校验."""
        pwd = v.get_secret_value()
        if len(pwd) < 8:
            raise ValueError("密码长度至少 8 位")
        if not any(c.isalpha() for c in pwd) or not any(c.isdigit() for c in pwd):
            raise ValueError("密码必须包含字母和数字")
        return v


def _build_frontend_url(path_with_query: str) -> str:
    """拼接前端验证/重置回跳地址."""
    from ipflow.config import get_settings
    base = get_settings().APP_BASE_URL.rstrip("/")
    return f"{base}/{path_with_query.lstrip('/')}"


@router.post(
    "/auth/verify-email/resend",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="重新发送邮箱验证邮件",
    description="向未验证邮箱的用户发送验证邮件；已验证或不存在均返回成功（防枚举）。",
)
@limiter.limit("3/hour")
async def resend_verification_email(
    request: Request,
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """重新发送邮箱验证邮件.

    限流：3 次/小时/IP。
    无论邮箱是否存在或已验证，均返回成功，防止邮箱枚举攻击。
    """
    user = await get_user_by_email(db, payload.email)
    # 仅当用户存在且未验证时才真正发送
    if user and not user.is_verified:
        from ipflow.core.action_token import create_action_token, PURPOSE_EMAIL_VERIFICATION
        from ipflow.services.email_service import send_email_verification

        token = create_action_token(str(user.id), PURPOSE_EMAIL_VERIFICATION)
        verify_url = _build_frontend_url(f"auth/verify-email?token={token}")
        try:
            await send_email_verification(user.email, user.username, verify_url)
        except Exception as e:  # noqa: BLE001 邮件失败不暴露给客户端
            logger.warning("发送验证邮件失败（to=%s）：%s", user.email, e)

    return SuccessResponse(code="SUCCESS", message="若该邮箱已注册且未验证，验证邮件已发送")


@router.post(
    "/auth/verify-email",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="验证邮箱",
    description="使用邮件中的令牌完成邮箱验证。",
)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """验证邮箱令牌."""
    from uuid import UUID
    from ipflow.core.action_token import verify_action_token, PURPOSE_EMAIL_VERIFICATION

    result = verify_action_token(payload.token, PURPOSE_EMAIL_VERIFICATION)
    if not result.is_valid:
        raise ValidationException(message=result.error or "验证失败")

    user = await get_user_by_id(db, UUID(result.user_id))
    if not user:
        raise NotFoundException(message="用户不存在")

    if user.is_verified:
        return SuccessResponse(code="SUCCESS", message="邮箱已验证，无需重复操作")

    user.is_verified = True
    await db.commit()

    return SuccessResponse(code="SUCCESS", message="邮箱验证成功")


@router.post(
    "/auth/forgot-password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="忘记密码",
    description="向注册邮箱发送密码重置链接；邮箱不存在时仍返回成功（防枚举）。",
)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """请求密码重置邮件.

    限流：3 次/小时/IP。
    无论邮箱是否存在，均返回成功，防止邮箱枚举攻击。
    """
    user = await get_user_by_email(db, payload.email)
    if user:
        from ipflow.core.action_token import create_action_token, PURPOSE_PASSWORD_RESET
        from ipflow.services.email_service import send_password_reset

        token = create_action_token(str(user.id), PURPOSE_PASSWORD_RESET)
        reset_url = _build_frontend_url(f"auth/reset-password?token={token}")
        try:
            await send_password_reset(user.email, user.username, reset_url)
        except Exception as e:  # noqa: BLE001 邮件失败不暴露给客户端
            logger.warning("发送重置密码邮件失败（to=%s）：%s", user.email, e)

    return SuccessResponse(code="SUCCESS", message="若该邮箱已注册，重置链接已发送")


@router.post(
    "/auth/reset-password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="重置密码",
    description="使用重置令牌设置新密码。",
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """使用令牌重置密码."""
    from uuid import UUID
    from ipflow.core.action_token import verify_action_token, PURPOSE_PASSWORD_RESET

    result = verify_action_token(payload.token, PURPOSE_PASSWORD_RESET)
    if not result.is_valid:
        raise ValidationException(message=result.error or "重置失败")

    user = await get_user_by_id(db, UUID(result.user_id))
    if not user:
        raise NotFoundException(message="用户不存在")

    user.hashed_password = get_password_hash(payload.new_password.get_secret_value())
    await db.commit()

    logger.info("用户 %s 已通过重置令牌修改密码", user.id)
    return SuccessResponse(code="SUCCESS", message="密码重置成功，请使用新密码登录")
