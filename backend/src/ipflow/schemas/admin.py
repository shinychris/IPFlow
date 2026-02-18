"""管理员Schema.

定义管理员相关的请求和响应模型。
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel

from ipflow.models import UserRole, UserStatus


# === Dashboard ===

class AdminDashboardStats(BaseModel):
    """管理后台统计数据."""
    total_users: int
    new_users_this_month: int
    total_organizations: int
    active_subscriptions: int
    revenue_this_month: Decimal
    total_projects: int


# === 用户管理 ===

class AdminUserResponse(BaseModel):
    """管理员用户响应."""
    id: UUID
    username: str
    email: str
    display_name: Optional[str]
    role: UserRole
    status: UserStatus
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    """管理员用户更新."""
    display_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    email_verified: Optional[bool] = None


# === 组织管理 ===

class AdminOrganizationResponse(BaseModel):
    """管理员组织响应."""
    id: UUID
    name: str
    slug: str
    plan_type: str
    max_projects: int
    max_storage_bytes: int
    max_members: int
    used_storage_bytes: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    member_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class AdminOrganizationUpdate(BaseModel):
    """管理员组织更新."""
    name: Optional[str] = None
    plan_type: Optional[str] = None
    max_projects: Optional[int] = None
    max_storage_bytes: Optional[int] = None
    max_members: Optional[int] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


# === 计划管理 ===

class AdminPlanResponse(BaseModel):
    """管理员计划响应."""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    price_monthly: Decimal
    price_yearly: Decimal
    currency: str
    features: List[str]
    limits: Dict[str, Any]
    is_active: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AdminPlanCreate(BaseModel):
    """创建计划请求."""
    name: str
    slug: str
    description: Optional[str] = None
    price_monthly: Decimal
    price_yearly: Decimal
    currency: str = "CNY"
    features: List[str] = []
    limits: Dict[str, Any] = {}
    is_active: bool = True
    is_public: bool = True


class AdminPlanUpdate(BaseModel):
    """更新计划请求."""
    name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    features: Optional[List[str]] = None
    limits: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


# === 审计日志 ===

class AdminAuditLogResponse(BaseModel):
    """审计日志响应."""
    id: UUID
    user_id: Optional[UUID]
    organization_id: Optional[UUID]
    action: str
    resource_type: str
    resource_id: Optional[UUID]
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminAuditLogQuery(BaseModel):
    """审计日志查询参数."""
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
