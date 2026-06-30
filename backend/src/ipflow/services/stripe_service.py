"""Stripe 支付服务.

基于 Stripe 官方 Python SDK（``stripe``）实现真实的支付下单与 Webhook 验签。
与微信/支付宝的模拟实现不同，本模块在未配置 ``STRIPE_SECRET_KEY`` 时**直接抛错**，
不会返回任何假支付链接，避免「无凭证也放行」的商业化风险。

设计要点：
- **Checkout Session**：创建一次性托管支付页，前端只需跳转到 ``checkout_url``，
  无需自行处理卡片信息，天然满足 PCI 合规。
- **价格映射**：Stripe 价格在 Stripe Dashboard 维护，本服务通过 ``plan_id + interval``
  映射到 Stripe Price ID（来自配置 ``STRIPE_PRICE_MAP``），避免在本库硬编码价格。
- **Webhook 验签**：使用 ``stripe.Webhook.construct_event`` 校验签名与时间戳，
  未配置 ``STRIPE_WEBHOOK_SECRET`` 时**拒绝**（安全默认）。
- **幂等**：订单号 ``order_no`` 作为 Stripe ``client_reference_id``，Webhook 据此回填本地订单。
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------- 配置读取（与 payment_service 保持一致的 env-first 风格） ----------

def _settings_get(key: str, default: Optional[str] = None) -> Optional[str]:
    """从环境变量读取 Stripe 凭证（隔离对 settings 的耦合）."""
    val = os.environ.get(key)
    return val if val else default


def stripe_secret_key() -> Optional[str]:
    """获取 Stripe Secret Key."""
    return _settings_get("STRIPE_SECRET_KEY")


def stripe_webhook_secret() -> Optional[str]:
    """获取 Stripe Webhook Signing Secret."""
    return _settings_get("STRIPE_WEBHOOK_SECRET")


def _parse_price_map() -> dict[str, dict[str, str]]:
    """解析 ``STRIPE_PRICE_MAP`` 配置.

    格式：``plan_id:monthly=price_xxx,plan_id:yearly=price_yyy``

    Returns:
        形如 ``{"starter": {"monthly": "price_xxx", "yearly": "price_yyy"}}`` 的映射
    """
    raw = _settings_get("STRIPE_PRICE_MAP") or ""
    result: dict[str, dict[str, str]] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item or "=" not in item:
            continue
        key, price_id = item.split("=", 1)
        key = key.strip()
        price_id = price_id.strip()
        if ":" in key:
            plan_id, interval = key.split(":", 1)
            result.setdefault(plan_id.strip(), {})[interval.strip()] = price_id
    return result


def get_stripe_price_id(plan_id: str, interval: str) -> Optional[str]:
    """根据 plan_id 与计费周期获取 Stripe Price ID."""
    return _parse_price_map().get(plan_id, {}).get(interval)


# ---------- Stripe 客户端（惰性初始化） ----------

def _get_stripe_client():
    """惰性获取已配置的 stripe 客户端.

    Returns:
        已设置 api_key 的 ``stripe`` 模块

    Raises:
        RuntimeError: 未配置 ``STRIPE_SECRET_KEY`` 或 stripe 包未安装
    """
    key = stripe_secret_key()
    if not key:
        raise RuntimeError(
            "Stripe 未配置 STRIPE_SECRET_KEY，无法发起真实支付。"
            "请在环境变量中配置后再启用 stripe 支付方式。"
        )
    try:
        import stripe  # type: ignore[import-untyped]
    except ImportError as e:  # pragma: no cover - 依赖缺失分支
        raise RuntimeError(
            "stripe 包未安装，请运行 `uv pip install stripe` 后重试"
        ) from e
    stripe.api_key = key
    return stripe


class StripeService:
    """Stripe 支付服务（Checkout Session 模式）."""

    def generate_order_no(self) -> str:
        """生成订单号（与 PaymentService 接口对齐）."""
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex[:6].upper()
        return f"IPF{timestamp}{random_str}"

    async def create_payment(
        self,
        user_id: str,
        plan_id: str,
        billing_interval: str,
        payment_method: str,
        amount: int,
        order_no: str,
        client_ip: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> dict[str, Any]:
        """创建 Stripe Checkout Session.

        Args:
            user_id: 用户ID
            plan_id: 计划ID（本地标识，用于映射 Stripe Price）
            billing_interval: 计费周期 (monthly/yearly)
            payment_method: 支付方式（固定 stripe）
            amount: 金额（分，仅用于本地记录，真实金额以 Stripe Price 为准）
            order_no: 本地订单号，写入 client_reference_id 供 Webhook 回填
            client_ip: 客户端IP（记录用）
            success_url: 支付成功回跳地址
            cancel_url: 支付取消回跳地址

        Returns:
            ``{"payment_method": "stripe", "checkout_url": ..., "order_no": ...}``

        Raises:
            RuntimeError: 未配置 STRIPE_SECRET_KEY 或对应的 Stripe Price
        """
        stripe = _get_stripe_client()

        # 映射到 Stripe Price
        price_id = get_stripe_price_id(plan_id, billing_interval)
        if not price_id:
            raise RuntimeError(
                f"Stripe Price 未配置：plan_id={plan_id} interval={billing_interval}。"
                f"请在 STRIPE_PRICE_MAP 中配置对应 Price ID。"
            )

        # 默认回跳地址兜底
        if not success_url:
            app_base = _settings_get("APP_BASE_URL") or "http://localhost:3000"
            success_url = f"{app_base}/dashboard/subscriptions?paid=1&order={order_no}"
        if not cancel_url:
            app_base = _settings_get("APP_BASE_URL") or "http://localhost:3000"
            cancel_url = f"{app_base}/dashboard/subscriptions?canceled=1"

        try:
            # stripe SDK 是同步的，在异步上下文中直接调用会阻塞事件循环；
            # Checkout Session 创建是低频操作，可接受短阻塞。生产可换 stripe.AsyncPaymentIntent。
            session = stripe.checkout.Session.create(
                mode="subscription" if billing_interval in ("monthly", "yearly") else "payment",
                line_items=[{"price": price_id, "quantity": 1}],
                client_reference_id=order_no,
                metadata={
                    "user_id": user_id,
                    "plan_id": plan_id,
                    "billing_interval": billing_interval,
                    "order_no": order_no,
                },
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except Exception as e:  # noqa: BLE001
            logger.error("Stripe Checkout Session 创建失败：%s", e)
            raise RuntimeError(f"Stripe 创建支付会话失败：{e}") from e

        return {
            "payment_method": "stripe",
            "checkout_url": session.url,
            "session_id": session.id,
            "order_no": order_no,
            "expires_at": None,  # Stripe Session 自带过期，本地不再维护
        }

    @staticmethod
    def verify_webhook(payload: bytes, signature: str) -> Optional[dict[str, Any]]:
        """验证 Stripe Webhook 签名并解析事件.

        Args:
            payload: 原始请求体（bytes）
            signature: ``Stripe-Signature`` 请求头

        Returns:
            解析后的 Stripe Event 对象（dict）；验签失败返回 ``None``
        """
        secret = stripe_webhook_secret()
        if not secret:
            logger.warning("Stripe Webhook 验签：未配置 STRIPE_WEBHOOK_SECRET，拒绝")
            return None
        try:
            stripe = _get_stripe_client()
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=secret,
            )
            return event
        except ValueError as e:
            logger.warning("Stripe Webhook 验签：无效载荷：%s", e)
            return None
        except Exception as e:  # noqa: BLE001 - stripe 抛 stripe.error.SignatureVerificationError 等
            logger.warning("Stripe Webhook 验签失败：%s", e)
            return None

    @staticmethod
    def extract_event_info(event: dict[str, Any]) -> dict[str, Any]:
        """从 Stripe Event 中提取本地需要的订单/订阅信息.

        Returns:
            ``{
              "event_type": "checkout.session.completed",
              "order_no": "IPF...",          # 来自 client_reference_id
              "stripe_session_id": "cs_test_...",
              "subscription_id": "sub_...",  # 订阅模式才有
              "customer_id": "cus_...",
              "amount_total": 19900,         # 分（Stripe 以「最小货币单位」返回）
              "currency": "cny",
              "raw": event,
            }
        """
        event_type = event.get("type")
        obj = (
            event.get("data", {}).get("object", {})
            if isinstance(event.get("data"), dict)
            else {}
        )
        return {
            "event_type": event_type,
            "order_no": obj.get("client_reference_id"),
            "stripe_session_id": obj.get("id"),
            "subscription_id": obj.get("subscription"),
            "customer_id": obj.get("customer"),
            "amount_total": obj.get("amount_total"),
            "currency": obj.get("currency"),
            "raw": event,
        }


# 工厂便捷方法
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """获取 StripeService 单例."""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService()
    return _stripe_service


def is_stripe_configured() -> bool:
    """Stripe 是否已完成基础配置（仅判断 Secret Key 是否存在）."""
    return stripe_secret_key() is not None
