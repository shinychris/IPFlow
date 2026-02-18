"""依赖注入模块.

提供 FastAPI 依赖函数。
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Header, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db.session import get_db
from ipflow.core.security import decode_access_token
from ipflow.models import User, UserRole, Organization, OrganizationMember


# OAuth2 认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """获取当前用户（可选）.
    
    从 JWT token 中解析用户ID，并从数据库获取用户信息。
    如果token无效或用户不存在，返回None而不是抛出异常。
    """
    if not token:
        return None
    
    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    return result.scalar_one_or_none()


async def require_active_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """要求用户已登录且处于活跃状态.
    
    如果用户未登录或非活跃状态，抛出 401 异常。
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if current_user.status != "active":
        raise HTTPException(
            status_code=403,
            detail="User account is not active",
        )
    
    return current_user


async def require_super_admin(
    current_user: User = Depends(require_active_user),
) -> User:
    """要求超级管理员权限."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Super admin access required",
        )
    return current_user


async def require_org_role(
    allowed_roles: Optional[list[UserRole]] = None,
    x_tenant_id: Optional[str] = Header(None),
    org_id: Optional[UUID] = Query(None),
    current_user: User = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """要求组织角色权限.
    
    Args:
        allowed_roles: 允许的角色列表，None表示允许所有角色
        x_tenant_id: 组织ID（通过Header传递）
        org_id: 组织ID（通过Query传递）
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        组织ID
        
    Raises:
        HTTPException: 如果没有权限
    """
    # 获取组织ID
    organization_id = org_id or (UUID(x_tenant_id) if x_tenant_id else None)
    
    if not organization_id:
        raise HTTPException(
            status_code=400,
            detail="Organization ID required (via X-Tenant-ID header or org_id query param)",
        )
    
    # 检查用户是否是组织成员
    from sqlalchemy import select
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=403,
            detail="Not a member of this organization",
        )
    
    # 检查角色权限
    if allowed_roles and member.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )
    
    return organization_id


async def get_current_tenant_id(
    x_tenant_id: Optional[str] = Header(None),
    org_id: Optional[UUID] = Query(None),
) -> Optional[UUID]:
    """获取当前租户ID（无需验证权限）.
    
    用于只读操作，不需要检查用户是否有权限访问该组织。
    """
    if org_id:
        return org_id
    if x_tenant_id:
        try:
            return UUID(x_tenant_id)
        except ValueError:
            pass
    return None
