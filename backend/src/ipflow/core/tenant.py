"""多租户上下文管理.

提供租户隔离功能。
"""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

from fastapi import Request, HTTPException, status

# 租户上下文变量
tenant_id_ctx: ContextVar[Optional[UUID]] = ContextVar("tenant_id", default=None)


class TenantContext:
    """租户上下文管理器.
    
    使用 ContextVar 实现请求级别的租户隔离。
    """
    
    @staticmethod
    def get_current_tenant_id() -> Optional[UUID]:
        """获取当前租户ID."""
        return tenant_id_ctx.get()
    
    @staticmethod
    def set_current_tenant_id(tenant_id: UUID) -> None:
        """设置当前租户ID."""
        tenant_id_ctx.set(tenant_id)
    
    @staticmethod
    def clear() -> None:
        """清除租户上下文."""
        tenant_id_ctx.set(None)


class TenantMiddleware:
    """租户中间件.
    
    从请求头中提取租户ID并设置上下文。
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI 中间件入口."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # 从请求头中提取租户ID
        headers = dict(scope.get("headers", []))
        tenant_header = headers.get(b"x-tenant-id", b"").decode()
        
        if tenant_header:
            try:
                tenant_id = UUID(tenant_header)
                TenantContext.set_current_tenant_id(tenant_id)
            except ValueError:
                pass  # 无效的UUID，忽略
        
        try:
            await self.app(scope, receive, send)
        finally:
            # 清理上下文
            TenantContext.clear()


async def get_tenant_id_from_request(request: Request) -> Optional[UUID]:
    """从请求中获取租户ID.
    
    优先从查询参数获取，其次从请求头获取。
    """
    # 从查询参数获取
    tenant_id_str = request.query_params.get("tenant_id")
    if tenant_id_str:
        try:
            return UUID(tenant_id_str)
        except ValueError:
            pass
    
    # 从请求头获取
    tenant_id_str = request.headers.get("x-tenant-id")
    if tenant_id_str:
        try:
            return UUID(tenant_id_str)
        except ValueError:
            pass
    
    # 从上下文获取
    return TenantContext.get_current_tenant_id()


async def require_tenant(
    request: Request,
) -> UUID:
    """要求必须提供租户ID.
    
    用于需要租户隔离的端点。
    
    Args:
        request: FastAPI 请求对象
        
    Returns:
        租户ID
        
    Raises:
        HTTPException: 如果未提供租户ID
    """
    tenant_id = await get_tenant_id_from_request(request)
    
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing tenant ID. Provide 'x-tenant-id' header or 'tenant_id' query parameter.",
        )
    
    return tenant_id


class TenantService:
    """租户服务.
    
    提供租户相关的业务逻辑。
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_user_organizations(self, user_id: UUID) -> list:
        """获取用户所属的所有组织."""
        from sqlalchemy import select
        from ipflow.models import Organization, OrganizationMember
        
        result = await self.db.execute(
            select(Organization)
            .join(OrganizationMember)
            .where(
                OrganizationMember.user_id == user_id,
                Organization.is_active == True,
                Organization.deleted_at.is_(None),
            )
        )
        return result.scalars().all()
    
    async def check_user_in_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """检查用户是否在组织中."""
        from sqlalchemy import select
        from ipflow.models import OrganizationMember
        
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def get_user_role_in_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> Optional[str]:
        """获取用户在组织中的角色."""
        from sqlalchemy import select
        from ipflow.models import OrganizationMember
        
        result = await self.db.execute(
            select(OrganizationMember.role).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            )
        )
        role = result.scalar_one_or_none()
        return role.value if role else None
