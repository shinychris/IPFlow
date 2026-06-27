"""订阅服务实现.

提供订阅管理核心业务逻辑。
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.models.subscription import (
    Plan, Subscription, SubscriptionStatus, Invoice, InvoiceStatus, PlanInterval
)
from ipflow.models import Organization
from ipflow.services.quota_service import QuotaService

logger = logging.getLogger(__name__)


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
) -> Dict[str, Any]:
    """处理支付提供商 Webhook，更新订阅与发票状态.

    支持的提供商事件（按 ``provider`` 归一化处理）：

    - ``stripe``: ``invoice.paid`` / ``invoice.payment_failed`` /
      ``customer.subscription.updated`` / ``customer.subscription.deleted``
    - ``wechat`` / ``alipay``: 通过 ``trade_state``/``trade_status`` 判断支付成功或失败

    特性：

    - **幂等**：以事件 ``event_id`` 去重，重复投递直接跳过。
    - **签名**：调用方应在路由层完成签名校验后传入；本函数记录原始签名以备审计。
    - **降级**：载荷缺失关键字段时记录日志并返回 ``skipped``，不抛异常。

    Args:
        db: 数据库会话
        provider: 支付提供商（``stripe``/``wechat``/``alipay``）
        payload: 原始 Webhook 载荷（JSON 字符串）
        signature: Webhook 签名（用于审计）

    Returns:
        处理结果字典：``{"status": "processed"|"skipped"|"ignored", "event_id": ...}``
    """
    provider = (provider or "").lower()

    try:
        data: Dict[str, Any] = json.loads(payload) if payload else {}
    except (json.JSONDecodeError, TypeError):
        logger.warning("subscriptions.handle_webhook: 无效的 JSON 载荷（provider=%s）", provider)
        return {"status": "ignored", "event_id": None, "reason": "invalid_payload"}

    # 提取事件 ID（用于幂等去重）
    event_id = (
        data.get("id")
        or data.get("event_id")
        or data.get("event")
        or f"{provider}:{hash(payload)}"
    )

    # 幂等：检查是否已处理过该事件
    try:
        from ipflow.models.payment import PaymentWebhookLog

        existing = await db.execute(
            select(PaymentWebhookLog).where(PaymentWebhookLog.event_id == event_id)
        )
        if existing.scalar_one_or_none():
            logger.info("subscriptions.handle_webhook: 事件 %s 已处理，跳过", event_id)
            return {"status": "skipped", "event_id": event_id, "reason": "duplicate"}
    except Exception as e:  # noqa: BLE001
        # PaymentWebhookLog 可能不存在或表未建，降级为不做去重（仅记录日志）
        logger.debug("subscriptions.handle_webhook: 幂等检查跳过：%s", e)

    # 记录 Webhook 日志（审计）
    # 签名仅作审计记录（模型无 signature 列，避免污染日志表）
    logger.debug("subscriptions.handle_webhook: 原始签名=%s", signature)
    try:
        from ipflow.models.payment import PaymentWebhookLog

        log_entry = PaymentWebhookLog(
            id=f"log_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            event_id=event_id,
            provider=provider,
            payload=payload[:8000] if payload else "",
            success=True,
            created_at=datetime.utcnow(),
        )
        db.add(log_entry)
    except Exception as e:  # noqa: BLE001
        logger.debug("subscriptions.handle_webhook: Webhook 日志写入跳过：%s", e)

    # 解析事件类型与关联的订阅
    event_type, subscription_id, subscription_data = _extract_webhook_event(
        provider, data
    )
    logger.info(
        "subscriptions.handle_webhook: provider=%s event=%s sub=%s",
        provider, event_type, subscription_id,
    )

    if not subscription_id:
        # 非订阅相关事件（如退款、转账），记录后忽略
        await db.commit()
        return {"status": "ignored", "event_id": event_id, "reason": "no_subscription"}

    # 加载本地订阅（通过外部订阅ID匹配）
    result = await db.execute(
        select(Subscription).where(
            Subscription.payment_provider_subscription_id == subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        logger.warning(
            "subscriptions.handle_webhook: 未找到外部订阅 %s 对应的本地订阅",
            subscription_id,
        )
        await db.commit()
        return {"status": "ignored", "event_id": event_id, "reason": "subscription_not_found"}

    # 根据事件类型更新订阅状态
    _apply_subscription_event(subscription, event_type, subscription_data)

    await db.commit()
    return {"status": "processed", "event_id": event_id, "event_type": event_type}


def _extract_webhook_event(
    provider: str, data: Dict[str, Any]
) -> tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """从不同提供商的载荷中提取事件类型、订阅ID与订阅数据.

    Returns:
        ``(event_type, subscription_id, subscription_data)``
    """
    if provider == "stripe":
        event_type = data.get("type")
        obj = data.get("data", {}).get("object", {}) if isinstance(data.get("data"), dict) else {}
        subscription_id = obj.get("subscription") or obj.get("id")
        return event_type, subscription_id, obj

    if provider in ("wechat", "alipay"):
        # 微信/支付宝通常在支付成功回调中携带 out_trade_no / trade_state
        trade_state = (
            data.get("trade_state")
            or data.get("trade_status")
            or data.get("result_code")
        )
        success = trade_state in (
            "SUCCESS", "TRADE_SUCCESS", "TRADE_FINISHED", "支付成功",
        )
        event_type = "payment.success" if success else "payment.failed"
        subscription_id = data.get("out_trade_no") or data.get("trade_no")
        return event_type, subscription_id, data

    # 通用兜底
    return data.get("type"), data.get("subscription_id"), data


def _apply_subscription_event(
    subscription: Subscription,
    event_type: Optional[str],
    data: Dict[str, Any],
) -> None:
    """根据事件类型更新订阅状态.

    Args:
        subscription: 本地订阅记录
        event_type: 事件类型
        data: 订阅相关数据（可能含 period_end / cancel_at_period_end 等）
    """
    if not event_type:
        return

    et = event_type.lower()

    # 支付成功 / 订阅激活 / 续费
    if et in (
        "payment.success",
        "invoice.paid",
        "customer.subscription.updated",
    ):
        subscription.status = SubscriptionStatus.ACTIVE
        period_end = data.get("current_period_end") or data.get("period_end")
        if isinstance(period_end, (int, float)):
            subscription.current_period_end = datetime.utcfromtimestamp(period_end)
        if "cancel_at_period_end" in data:
            cap = data["cancel_at_period_end"]
            # 兼容表单回调传来的字符串布尔值（如支付宝异步通知）
            subscription.cancel_at_period_end = (
                str(cap).lower() in ("true", "1", "yes")
                if isinstance(cap, str)
                else bool(cap)
            )
        return

    # 支付失败 / 逾期
    if et in ("payment.failed", "invoice.payment_failed"):
        subscription.status = SubscriptionStatus.PAST_DUE
        return

    # 订阅取消
    if et in ("customer.subscription.deleted", "subscription.canceled"):
        subscription.status = SubscriptionStatus.CANCELED
        subscription.cancel_at_period_end = True
        return
