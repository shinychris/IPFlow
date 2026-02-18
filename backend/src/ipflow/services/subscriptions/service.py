"""订阅服务实现.

提供订阅管理核心业务逻辑。
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.models.subscription import (
    Plan, Subscription, SubscriptionStatus, Invoice, InvoiceStatus, PlanInterval
)
from ipflow.models import Organization
from ipflow.services.quota_service import QuotaService


async def list_plans(db: AsyncSession, public_only: bool = True) -> List[Plan]:
    """获取可用计划列表."""
    query = select(Plan).where(Plan.is_active == True)
    if public_only:
        query = query.where(Plan.is_public == True)
    query = query.order_by(Plan.price_monthly)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_plan(db: AsyncSession, plan_id: UUID) -> Optional[Plan]:
    """获取计划详情."""
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalar_one_or_none()


async def get_organization_subscription(
    db: AsyncSession,
    organization_id: UUID
) -> Optional[Subscription]:
    """获取组织当前订阅."""
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.organization_id == organization_id,
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING,
                SubscriptionStatus.PAST_DUE
            ])
        )
        .order_by(desc(Subscription.created_at))
    )
    return result.scalar_one_or_none()


async def create_subscription(
    db: AsyncSession,
    organization_id: UUID,
    plan_id: UUID,
    interval: str = "monthly",
    user_id: Optional[UUID] = None,
) -> Subscription:
    """创建订阅."""
    # 检查计划
    plan = await get_plan(db, plan_id)
    if not plan:
        raise ValueError("Plan not found")
    
    # 检查是否已有活动订阅
    existing = await get_organization_subscription(db, organization_id)
    if existing:
        raise ValueError("Organization already has an active subscription")
    
    # 计算周期
    now = datetime.utcnow()
    if interval == "yearly":
        period_end = now + timedelta(days=365)
    else:
        period_end = now + timedelta(days=30)
    
    # 创建订阅
    subscription = Subscription(
        organization_id=organization_id,
        plan_id=plan_id,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=now,
        current_period_end=period_end,
    )
    
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    
    # 更新组织的计划和限额
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    org = result.scalar_one()
    org.plan_type = plan.slug
    if plan.limits:
        org.max_projects = plan.limits.get("max_projects", org.max_projects)
        org.max_storage_bytes = plan.limits.get("max_storage_gb", 1) * 1024 ** 3
        org.max_members = plan.limits.get("max_members", org.max_members)
    
    await db.commit()
    
    return subscription


async def update_subscription(
    db: AsyncSession,
    organization_id: UUID,
    plan_id: Optional[UUID] = None,
    cancel_at_period_end: Optional[bool] = None,
) -> Subscription:
    """更新订阅."""
    subscription = await get_organization_subscription(db, organization_id)
    if not subscription:
        raise ValueError("No active subscription found")
    
    if plan_id:
        # 升级/降级计划
        plan = await get_plan(db, plan_id)
        if not plan:
            raise ValueError("Plan not found")
        
        subscription.plan_id = plan_id
        
        # 更新组织的限额
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one()
        org.plan_type = plan.slug
        if plan.limits:
            org.max_projects = plan.limits.get("max_projects", org.max_projects)
            org.max_storage_bytes = plan.limits.get("max_storage_gb", 1) * 1024 ** 3
            org.max_members = plan.limits.get("max_members", org.max_members)
    
    if cancel_at_period_end is not None:
        subscription.cancel_at_period_end = cancel_at_period_end
    
    subscription.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(subscription)
    
    return subscription


async def cancel_subscription(
    db: AsyncSession,
    organization_id: UUID,
    at_period_end: bool = True,
) -> Subscription:
    """取消订阅."""
    subscription = await get_organization_subscription(db, organization_id)
    if not subscription:
        raise ValueError("No active subscription found")
    
    if at_period_end:
        subscription.cancel_at_period_end = True
    else:
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.utcnow()
    
    subscription.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(subscription)
    
    return subscription


async def list_invoices(
    db: AsyncSession,
    organization_id: UUID,
    limit: int = 10,
) -> List[Invoice]:
    """获取组织发票列表."""
    result = await db.execute(
        select(Invoice)
        .where(Invoice.organization_id == organization_id)
        .order_by(desc(Invoice.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def get_usage_stats(db: AsyncSession, organization_id: UUID) -> dict:
    """获取资源使用统计."""
    quota_service = QuotaService(db)
    return await quota_service.get_usage_stats(organization_id)


async def handle_webhook(
    db: AsyncSession,
    provider: str,
    payload: str,
    signature: str,
) -> None:
    """处理支付提供商Webhook."""
    # 这是一个占位实现，实际应根据不同的支付提供商处理事件
    # 例如 Stripe: invoice.paid, invoice.payment_failed, subscription.updated 等
    pass
