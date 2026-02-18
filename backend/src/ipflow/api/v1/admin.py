"""管理员API.

提供系统管理功能（仅限超级管理员）。
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db.session import get_db
from ipflow.dependencies import get_current_user, require_super_admin
from ipflow.models import (
    User, UserRole, UserStatus,
    Organization,
    Plan, Subscription, Invoice,
    AuditLog,
    Project,
)
from ipflow.schemas.admin import (
    AdminDashboardStats,
    AdminUserResponse,
    AdminUserUpdate,
    AdminOrganizationResponse,
    AdminOrganizationUpdate,
    AdminPlanCreate,
    AdminPlanUpdate,
    AdminPlanResponse,
    AdminAuditLogResponse,
    AdminAuditLogQuery,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardStats)
async def get_dashboard_stats(
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取管理后台统计数据."""
    # 用户统计
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()
    
    result = await db.execute(
        select(func.count(User.id)).where(
            User.created_at >= datetime.utcnow().replace(day=1)
        )
    )
    new_users_this_month = result.scalar()
    
    # 组织统计
    result = await db.execute(select(func.count(Organization.id)))
    total_organizations = result.scalar()
    
    # 订阅统计
    result = await db.execute(
        select(func.count(Subscription.id)).where(
            Subscription.status == "active"
        )
    )
    active_subscriptions = result.scalar()
    
    result = await db.execute(
        select(func.sum(Invoice.amount_paid)).where(
            Invoice.status == "paid",
            Invoice.created_at >= datetime.utcnow().replace(day=1)
        )
    )
    revenue_this_month = result.scalar() or 0
    
    # 项目统计
    result = await db.execute(select(func.count(Project.id)))
    total_projects = result.scalar()
    
    return AdminDashboardStats(
        total_users=total_users,
        new_users_this_month=new_users_this_month,
        total_organizations=total_organizations,
        active_subscriptions=active_subscriptions,
        revenue_this_month=revenue_this_month,
        total_projects=total_projects,
    )


# === 用户管理 ===

@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表（分页）."""
    query = select(User).order_by(desc(User.created_at))
    
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.display_name.ilike(f"%{search}%"))
        )
    
    if role:
        query = query.where(User.role == role)
    
    if status:
        query = query.where(User.status == status)
    
    # 分页
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()
    
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return users


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: UUID,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取用户详情."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: UUID,
    data: AdminUserUpdate,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除用户."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "User deleted successfully"}


# === 组织管理 ===

@router.get("/organizations", response_model=List[AdminOrganizationResponse])
async def list_organizations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    plan_type: Optional[str] = None,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取组织列表（分页）."""
    query = select(Organization).order_by(desc(Organization.created_at))
    
    if search:
        query = query.where(
            (Organization.name.ilike(f"%{search}%")) |
            (Organization.slug.ilike(f"%{search}%"))
        )
    
    if plan_type:
        query = query.where(Organization.plan_type == plan_type)
    
    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    return result.scalars().all()


@router.get("/organizations/{org_id}", response_model=AdminOrganizationResponse)
async def get_organization(
    org_id: UUID,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取组织详情."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return org


@router.patch("/organizations/{org_id}", response_model=AdminOrganizationResponse)
async def update_organization(
    org_id: UUID,
    data: AdminOrganizationUpdate,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新组织信息."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)
    
    org.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(org)
    
    return org


@router.delete("/organizations/{org_id}")
async def delete_organization(
    org_id: UUID,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除组织."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # 软删除
    org.deleted_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Organization deleted successfully"}


# === 计划管理 ===

@router.get("/plans", response_model=List[AdminPlanResponse])
async def list_plans(
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取所有计划."""
    result = await db.execute(select(Plan).order_by(Plan.price_monthly))
    return result.scalars().all()


@router.post("/plans", response_model=AdminPlanResponse)
async def create_plan(
    data: AdminPlanCreate,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建新计划."""
    plan = Plan(**data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.patch("/plans/{plan_id}", response_model=AdminPlanResponse)
async def update_plan(
    plan_id: UUID,
    data: AdminPlanUpdate,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新计划."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    plan.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(plan)
    
    return plan


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: UUID,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除计划."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # 检查是否有活跃订阅
    result = await db.execute(
        select(func.count(Subscription.id)).where(Subscription.plan_id == plan_id)
    )
    if result.scalar() > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete plan with active subscriptions"
        )
    
    await db.delete(plan)
    await db.commit()
    
    return {"message": "Plan deleted successfully"}


# === 审计日志 ===

@router.get("/audit-logs", response_model=List[AdminAuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    query: AdminAuditLogQuery = Depends(),
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取审计日志."""
    from ipflow.models.audit import AuditLogService
    
    service = AuditLogService(db)
    logs = await service.get_logs(
        organization_id=query.organization_id,
        user_id=query.user_id,
        action=query.action,
        resource_type=query.resource_type,
        start_date=query.start_date,
        end_date=query.end_date,
        limit=per_page,
        offset=(page - 1) * per_page,
    )
    
    return logs
