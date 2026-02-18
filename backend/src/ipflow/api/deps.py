"""API 依赖模块.

提供 FastAPI 依赖注入函数。
"""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db import get_db
from ipflow.models.user import User, UserStatus
from ipflow.core.security import verify_access_token


async def get_current_user(
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前认证用户.
    
    从 Authorization 请求头中解析 JWT 令牌并验证。
    
    Args:
        authorization: Authorization 请求头
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 认证失败
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 解析 Bearer Token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证头格式",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # 验证令牌
    try:
        user_id = verify_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无效的令牌: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户
    from uuid import UUID
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def require_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求用户处于活跃状态.
    
    Args:
        current_user: 当前认证用户
        
    Returns:
        活跃的用户对象
        
    Raises:
        HTTPException: 用户未激活
    """
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号未激活或已被禁用",
        )
    
    return current_user


async def require_admin_user(
    current_user: User = Depends(require_active_user),
) -> User:
    """要求管理员权限.
    
    Args:
        current_user: 当前活跃用户
        
    Returns:
        管理员用户对象
        
    Raises:
        HTTPException: 用户不是管理员
    """
    from ipflow.models.user import UserRole
    
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    
    return current_user
