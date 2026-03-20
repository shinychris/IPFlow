"""订阅与计费API.

提供订阅管理、计划查询、发票查看等功能。
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.db.session import get_db
from ipflow.dependencies import get_current_user
from ipflow.models import User, UserRole

# Helper to wrap require_org_role for use with FastAPI Depends
def require_org_role_dep(allowed_roles=None):
    async def _dep(
        x_tenant_id: str = Header(None),
        org_id: UUID = Query(None),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> UUID:
        from ipflow.dependencies import require_org_role
        return await require_org_role(allowed_roles, x_tenant_id, org_id, current_user, db)
    return _dep
from ipflow.services import (
    list_plans as list_plans_service,
    get_plan as get_plan_service,
    get_organization_subscription,
    create_subscription as create_subscription_service,
    update_subscription as update_subscription_service,
    cancel_subscription as cancel_subscription_service,
    list_invoices as list_invoices_service,
    get_usage_stats as get_usage_stats_service,
    handle_webhook as handle_webhook_service,
)
from ipflow.schemas.subscription import (
    PlanResponse,
    SubscriptionResponse,
    SubscriptionCreate,
    SubscriptionUpdate,
    InvoiceResponse,
    UsageStatsResponse,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=List[PlanResponse])
async def list_plans(
    public_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """获取可用计划列表."""
    plans = await list_plans_service(db, public_only=public_only)
    return plans


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取计划详情."""
    plan = await get_plan_service(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.get("/current", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    current_org: UUID = Depends(require_org_role_dep()),
    db: AsyncSession = Depends(get_db),
):
    """获取当前组织的订阅."""
    subscription = await get_organization_subscription(db, current_org)
    return subscription


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    data: SubscriptionCreate,
    current_org: UUID = Depends(require_org_role_dep([UserRole.ADMIN])),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建订阅."""
    try:
        subscription = await create_subscription_service(
            db,
            organization_id=current_org,
            plan_id=data.plan_id,
            interval=data.interval,
            user_id=current_user.id,
        )
        return subscription
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("", response_model=SubscriptionResponse)
async def update_subscription(
    data: SubscriptionUpdate,
    current_org: UUID = Depends(require_org_role_dep([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """更新订阅（升级/降级/取消）."""
    try:
        subscription = await update_subscription_service(
            db,
            organization_id=current_org,
            plan_id=data.plan_id,
            cancel_at_period_end=data.cancel_at_period_end,
        )
        return subscription
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    at_period_end: bool = True,
    current_org: UUID = Depends(require_org_role_dep([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """取消订阅."""
    try:
        subscription = await cancel_subscription_service(
            db,
            organization_id=current_org,
            at_period_end=at_period_end,
        )
        return subscription
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    limit: int = Query(10, ge=1, le=100),
    current_org: UUID = Depends(require_org_role_dep()),
    db: AsyncSession = Depends(get_db),
):
    """获取组织发票列表."""
    invoices = await list_invoices_service(db, current_org, limit=limit)
    return invoices


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    current_org: UUID = Depends(require_org_role_dep()),
    db: AsyncSession = Depends(get_db),
):
    """获取资源使用统计."""
    stats = await get_usage_stats_service(db, current_org)
    return stats


@router.post("/webhook/{provider}")
async def handle_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """处理支付提供商Webhook."""
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    await handle_webhook_service(
        db,
        provider=provider,
        payload=payload.decode(),
        signature=signature,
    )
    return {"status": "ok"}
