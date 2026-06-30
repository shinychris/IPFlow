"""支付 API 端点."""

from datetime import datetime, timedelta
import hashlib
import json
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipflow.api.deps import get_current_user
from ipflow.db.session import get_db
from ipflow.models.payment import (
    PaymentOrder,
    PaymentOrderCreate,
    PaymentOrderResponse,
    PaymentStatus,
    PaymentStatusResponse,
    PaymentWebhookLog,
)
from ipflow.models.user import User
from ipflow.services.payment_service import PaymentServiceFactory

router = APIRouter(prefix="/payments", tags=["payments"])


def _build_event_id(provider: str, order_no: str, status: str, payload: str) -> str:
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{provider}:{order_no}:{status}:{payload_hash}"


async def _is_duplicate_event(db: AsyncSession, event_id: str) -> bool:
    result = await db.execute(
        select(PaymentWebhookLog).where(PaymentWebhookLog.event_id == event_id)
    )
    return result.scalar_one_or_none() is not None


async def _record_webhook_event(
    db: AsyncSession,
    *,
    event_id: str,
    provider: str,
    payment_id: str | None,
    order_no: str | None,
    payload: str,
    success: bool,
    error_message: str | None = None,
) -> None:
    webhook_log = PaymentWebhookLog(
        id=f"log_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        payment_id=payment_id,
        order_no=order_no,
        event_id=event_id,
        provider=provider,
        payload=payload,
        success=success,
        error_message=error_message,
    )
    db.add(webhook_log)
    await db.commit()


@router.post("/create", response_model=PaymentOrderResponse)
async def create_payment(
    data: PaymentOrderCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建支付订单."""
    # 获取计划价格
    plan_pricing = {
        "single": {"monthly": 1900, "yearly": 1900},  # 按次付费，兼容 billing_interval 字段
        "starter": {"monthly": 4900, "yearly": 49000},  # 分为单位
        "professional": {"monthly": 19900, "yearly": 199000},
        "enterprise": {"monthly": 99900, "yearly": 999000},
        "agency": {"monthly": 199900, "yearly": 1999000},
    }

    if data.plan_id not in plan_pricing:
        raise HTTPException(status_code=400, detail="Invalid plan ID")

    amount = plan_pricing[data.plan_id][data.billing_interval.value]

    # 获取支付服务
    try:
        payment_service = PaymentServiceFactory.get_service(data.payment_method.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # 生成订单号
    order_no = payment_service.generate_order_no()
    payment_id = f"pay_{datetime.now().strftime('%Y%m%d%H%M%S')}_{order_no[-6:]}"

    # 获取客户端IP
    client_ip = request.client.host if request.client else "127.0.0.1"

    # 创建支付订单记录
    payment_order = PaymentOrder(
        id=payment_id,
        order_no=order_no,
        user_id=current_user.id,
        plan_id=data.plan_id,
        plan_name=data.plan_id.capitalize(),
        billing_interval=data.billing_interval,
        payment_method=data.payment_method,
        amount=amount,
        currency="CNY",
        status=PaymentStatus.PENDING,
        expires_at=datetime.now() + timedelta(minutes=30),
    )
    db.add(payment_order)
    await db.commit()
    await db.refresh(payment_order)

    # 调用支付服务创建支付
    try:
        # Stripe 需要 success_url / cancel_url；其他方式忽略这两个字段
        create_kwargs: dict = dict(
            user_id=str(current_user.id),
            plan_id=data.plan_id,
            billing_interval=data.billing_interval.value,
            payment_method=data.payment_method.value,
            amount=amount,
            order_no=order_no,
            client_ip=client_ip,
        )
        if data.payment_method.value == "stripe":
            create_kwargs["success_url"] = data.success_url
            create_kwargs["cancel_url"] = data.cancel_url

        payment_result = await payment_service.create_payment(**create_kwargs)

        # 更新订单信息（兼容 wechat qr_code / alipay pay_url / stripe checkout_url）
        payment_order.qr_code = payment_result.get("qr_code")
        payment_order.pay_url = payment_result.get("pay_url")
        # Stripe Checkout 跳转地址，复用 pay_url 字段存放，便于前端统一处理
        checkout_url = payment_result.get("checkout_url")
        if checkout_url:
            payment_order.pay_url = checkout_url
            # 记录 Stripe Session ID 到 extra_data 便于对账
            extra = json.loads(payment_order.extra_data) if payment_order.extra_data else {}
            extra["stripe_session_id"] = payment_result.get("session_id")
            payment_order.extra_data = json.dumps(extra, ensure_ascii=False)
        await db.commit()
        await db.refresh(payment_order)

    except Exception as exc:
        # 创建支付失败，删除订单
        await db.delete(payment_order)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(exc)}") from exc

    return PaymentOrderResponse(
        id=payment_order.id,
        order_no=payment_order.order_no,
        amount=payment_order.amount,
        currency=payment_order.currency,
        status=payment_order.status,
        payment_method=payment_order.payment_method,
        qr_code=payment_order.qr_code,
        pay_url=payment_order.pay_url,
        expires_at=payment_order.expires_at,
        plan={
            "id": payment_order.plan_id,
            "name": payment_order.plan_name,
        },
    )


@router.get("/{order_id}/status", response_model=PaymentStatusResponse)
async def get_payment_status(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询支付状态"""
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.id == order_id,
            PaymentOrder.user_id == current_user.id,
        )
    )
    payment_order = result.scalar_one_or_none()

    if not payment_order:
        raise HTTPException(status_code=404, detail="Payment order not found")

    return PaymentStatusResponse(
        order_id=payment_order.id,
        status=payment_order.status,
        paid_at=payment_order.paid_at,
    )


@router.post("/webhook/wechat")
async def wechat_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """微信支付回调（sandbox/mock 可用实现）."""
    # 获取回调数据
    data = await request.json()
    payload_str = str(data)

    # 获取订单号
    order_no = data.get("out_trade_no") or data.get("resource", {}).get("ciphertext", {})
    if isinstance(order_no, dict):
        order_no = order_no.get("out_trade_no")

    if not order_no:
        return {"code": "FAIL", "message": "Missing order_no"}

    # 查找订单
    result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == order_no))
    payment_order = result.scalar_one_or_none()

    if not payment_order:
        return {"code": "FAIL", "message": "Order not found"}

    trade_state = data.get("trade_state", data.get("event_type", "UNKNOWN"))
    event_id = _build_event_id("wechat", order_no, trade_state, payload_str)
    if await _is_duplicate_event(db, event_id):
        return {"code": "SUCCESS", "message": "Duplicate ignored"}

    # 验证签名（生产环境使用微信平台证书；沙箱可设 PAYMENT_SKIP_SIGNATURE_VERIFY）
    payment_service = PaymentServiceFactory.get_wechat_service()
    is_valid = await payment_service.verify_payment(payment_order.id, data)

    if not is_valid:
        await _record_webhook_event(
            db,
            event_id=event_id,
            provider="wechat",
            payment_id=payment_order.id,
            order_no=order_no,
            payload=payload_str,
            success=False,
            error_message="Invalid signature",
        )
        return {"code": "FAIL", "message": "Invalid signature"}

    if trade_state in ("SUCCESS", "TRANSACTION.SUCCESS"):
        payment_order.status = PaymentStatus.COMPLETED
        payment_order.paid_at = datetime.now()
        payment_order.transaction_id = data.get("transaction_id")

    elif trade_state in ("CLOSED", "PAYERROR", "TRANSACTION.CLOSED"):
        payment_order.status = PaymentStatus.FAILED

    payment_order.updated_at = datetime.now()
    await db.commit()
    await _record_webhook_event(
        db,
        event_id=event_id,
        provider="wechat",
        payment_id=payment_order.id,
        order_no=order_no,
        payload=payload_str,
        success=True,
    )

    return {"code": "SUCCESS", "message": "OK"}


@router.post("/webhook/alipay")
async def alipay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """支付宝回调（sandbox/mock 可用实现）."""
    # 获取回调数据
    data = await request.body()
    payload_str = data.decode("utf-8")

    # 解析表单数据
    params = urllib.parse.parse_qs(payload_str)
    order_no = params.get("out_trade_no", [None])[0]

    if not order_no:
        return {"success": False, "message": "Missing order_no"}

    # 查找订单
    result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == order_no))
    payment_order = result.scalar_one_or_none()

    if not payment_order:
        return {"success": False, "message": "Order not found"}

    trade_status = params.get("trade_status", [None])[0] or "UNKNOWN"
    event_id = _build_event_id("alipay", order_no, trade_status, payload_str)
    if await _is_duplicate_event(db, event_id):
        return {"success": True, "message": "Duplicate ignored"}

    # 验证签名（生产环境使用支付宝公钥；沙箱可设 PAYMENT_SKIP_SIGNATURE_VERIFY）
    payment_service = PaymentServiceFactory.get_alipay_service()
    is_valid = await payment_service.verify_payment(payment_order.id, params)

    if not is_valid:
        await _record_webhook_event(
            db,
            event_id=event_id,
            provider="alipay",
            payment_id=payment_order.id,
            order_no=order_no,
            payload=payload_str,
            success=False,
            error_message="Invalid signature",
        )
        return {"success": False, "message": "Invalid signature"}

    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        payment_order.status = PaymentStatus.COMPLETED
        payment_order.paid_at = datetime.now()
        payment_order.transaction_id = params.get("trade_no", [None])[0]
    elif trade_status in ("TRADE_CLOSED", "TRADE_FINISHED_WITHOUT_SUCCESS"):
        payment_order.status = PaymentStatus.FAILED

    payment_order.updated_at = datetime.now()
    await db.commit()
    await _record_webhook_event(
        db,
        event_id=event_id,
        provider="alipay",
        payment_id=payment_order.id,
        order_no=order_no,
        payload=payload_str,
        success=True,
    )

    return {"success": True}


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Stripe Webhook 回调.

    使用 ``STRIPE_WEBHOOK_SECRET`` 校验签名，校验通过后根据事件类型：
    - ``checkout.session.completed``：标记订单 ``COMPLETED``，激活订阅
    - ``checkout.session.expired``：标记订单 ``FAILED``
    - 其余订阅事件（``invoice.*`` / ``customer.subscription.*``）转交订阅服务处理

    幂等：以 Stripe Event ID 去重，重复投递直接跳过。
    验签失败一律返回 400（不泄露内部状态）。
    """
    from ipflow.services.stripe_service import get_stripe_service
    from ipflow.services.subscriptions import service as subs_service

    raw_body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    # 验签（未配置 STRIPE_WEBHOOK_SECRET 时 verify_webhook 返回 None）
    event = get_stripe_service().verify_webhook(payload=raw_body, signature=signature)
    if event is None:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    payload_str = raw_body.decode("utf-8", errors="replace")
    event_id = event.get("id") or _build_event_id("stripe", "unknown", "unknown", payload_str)

    # 幂等
    if await _is_duplicate_event(db, event_id):
        return {"received": True, "message": "Duplicate ignored"}

    info = get_stripe_service().extract_event_info(event)
    event_type = info.get("event_type")
    order_no = info.get("order_no")

    # 尝试回填本地订单（checkout.session.* 事件携带 client_reference_id=order_no）
    payment_order = None
    if order_no:
        result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        )
        payment_order = result.scalar_one_or_none()

    if event_type == "checkout.session.completed":
        if payment_order:
            payment_order.status = PaymentStatus.COMPLETED
            payment_order.paid_at = datetime.now()
            payment_order.transaction_id = info.get("stripe_session_id")
            payment_order.updated_at = datetime.now()
            await db.commit()
    elif event_type == "checkout.session.expired":
        if payment_order:
            payment_order.status = PaymentStatus.FAILED
            payment_order.updated_at = datetime.now()
            await db.commit()

    # 订阅相关事件转交订阅服务（含幂等、状态映射）
    if event_type and (
        event_type.startswith("invoice.")
        or event_type.startswith("customer.subscription.")
    ):
        try:
            await subs_service.handle_webhook(
                db=db,
                provider="stripe",
                payload=json.dumps(event, ensure_ascii=False),
                signature=signature,
            )
        except Exception as exc:  # noqa: BLE001 - 订阅处理失败不应影响订单状态已更新
            import logging
            logging.getLogger(__name__).warning(
                "Stripe webhook 订阅事件处理失败：%s", exc
            )

    # 记录 Webhook 日志（审计）
    await _record_webhook_event(
        db,
        event_id=event_id,
        provider="stripe",
        payment_id=payment_order.id if payment_order else None,
        order_no=order_no,
        payload=payload_str,
        success=True,
    )

    return {"received": True}
