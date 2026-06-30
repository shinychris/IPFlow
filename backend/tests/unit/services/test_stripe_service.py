"""Stripe 支付服务单元测试.

覆盖：
- 价格映射解析
- 未配置凭证时的安全默认（拒绝）
- create_payment 的 Stripe SDK mock 验证
- webhook 验签的拒绝/通过分支
"""
# pylint: disable=import-error,redefined-outer-name,unused-argument
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ipflow.services.stripe_service import (
    StripeService,
    _parse_price_map,
    get_stripe_price_id,
    is_stripe_configured,
    stripe_secret_key,
    stripe_webhook_secret,
)


# ---------- 配置 / 价格映射 ----------

class TestPriceMapParsing:
    """STRIPE_PRICE_MAP 解析."""

    def test_parse_simple(self, monkeypatch):
        monkeypatch.setenv(
            "STRIPE_PRICE_MAP",
            "starter:monthly=price_abc,starter:yearly=price_def,professional:monthly=price_ghi",
        )
        m = _parse_price_map()
        assert m["starter"]["monthly"] == "price_abc"
        assert m["starter"]["yearly"] == "price_def"
        assert m["professional"]["monthly"] == "price_ghi"

    def test_parse_empty(self, monkeypatch):
        monkeypatch.delenv("STRIPE_PRICE_MAP", raising=False)
        assert _parse_price_map() == {}

    def test_parse_garbage_ignored(self, monkeypatch):
        monkeypatch.setenv("STRIPE_PRICE_MAP", "garbage_no_equals, ,a:b=c")
        m = _parse_price_map()
        assert m == {"a": {"b": "c"}}

    def test_get_stripe_price_id(self, monkeypatch):
        monkeypatch.setenv(
            "STRIPE_PRICE_MAP",
            "starter:monthly=price_abc,starter:yearly=price_def",
        )
        assert get_stripe_price_id("starter", "monthly") == "price_abc"
        assert get_stripe_price_id("starter", "yearly") == "price_def"
        assert get_stripe_price_id("starter", "weekly") is None
        assert get_stripe_price_id("enterprise", "monthly") is None


class TestConfigPresence:
    """凭证存在性判断（安全默认）."""

    def test_is_configured_false_when_no_key(self, monkeypatch):
        monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
        assert is_stripe_configured() is False
        assert stripe_secret_key() is None

    def test_is_configured_true(self, monkeypatch):
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")
        assert is_stripe_configured() is True
        assert stripe_secret_key() == "sk_test_xxx"

    def test_webhook_secret(self, monkeypatch):
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_xxx")
        assert stripe_webhook_secret() == "whsec_xxx"


# ---------- create_payment ----------

class TestCreatePayment:
    """create_payment 行为."""

    def test_raises_when_no_secret_key(self, monkeypatch):
        """未配置 STRIPE_SECRET_KEY 时必须抛错，不能返回假支付链接."""
        monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
        svc = StripeService()
        with pytest.raises(RuntimeError, match="STRIPE_SECRET_KEY"):
            asyncio.run(svc.create_payment(
                user_id="u1", plan_id="starter", billing_interval="monthly",
                payment_method="stripe", amount=4900, order_no="IPF1",
                client_ip="127.0.0.1",
            ))

    def test_raises_when_no_price_mapping(self, monkeypatch):
        """配置了 key 但未映射对应 Price 时也必须报错."""
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")
        monkeypatch.delenv("STRIPE_PRICE_MAP", raising=False)
        # mock stripe client（避免依赖真实 stripe 包，聚焦 price 映射逻辑）
        with patch(
            "ipflow.services.stripe_service._get_stripe_client",
            return_value=MagicMock(),
        ):
            svc = StripeService()
            with pytest.raises(RuntimeError, match="Stripe Price 未配置"):
                asyncio.run(svc.create_payment(
                    user_id="u1", plan_id="starter", billing_interval="monthly",
                    payment_method="stripe", amount=4900, order_no="IPF1",
                    client_ip="127.0.0.1",
                ))

    def test_create_session_calls_stripe_sdk(self, monkeypatch):
        """配置齐全时调用 stripe.checkout.Session.create 并返回 checkout_url."""
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")
        monkeypatch.setenv("STRIPE_PRICE_MAP", "starter:monthly=price_abc")

        fake_session = MagicMock()
        fake_session.url = "https://checkout.stripe.com/c/cs_test_123"
        fake_session.id = "cs_test_123"

        fake_stripe = MagicMock()
        fake_stripe.checkout.Session.create.return_value = fake_session

        with patch("ipflow.services.stripe_service._get_stripe_client", return_value=fake_stripe):
            svc = StripeService()
            result = asyncio.run(svc.create_payment(
                user_id="u1", plan_id="starter", billing_interval="monthly",
                payment_method="stripe", amount=4900, order_no="IPFOO",
                client_ip="127.0.0.1",
            ))

        assert result["payment_method"] == "stripe"
        assert result["checkout_url"] == "https://checkout.stripe.com/c/cs_test_123"
        assert result["session_id"] == "cs_test_123"
        assert result["order_no"] == "IPFOO"

        # 验证 SDK 调用参数
        call_kwargs = fake_stripe.checkout.Session.create.call_args.kwargs
        assert call_kwargs["client_reference_id"] == "IPFOO"
        assert call_kwargs["line_items"] == [{"price": "price_abc", "quantity": 1}]
        assert call_kwargs["mode"] == "subscription"
        assert call_kwargs["metadata"]["plan_id"] == "starter"

    def test_create_payment_default_success_cancel_url(self, monkeypatch):
        """未传 success/cancel_url 时用 APP_BASE_URL 兜底."""
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")
        monkeypatch.setenv("STRIPE_PRICE_MAP", "starter:monthly=price_abc")
        monkeypatch.setenv("APP_BASE_URL", "https://app.example.com")

        fake_session = MagicMock()
        fake_session.url = "https://checkout.stripe.com/x"
        fake_session.id = "cs_x"
        fake_stripe = MagicMock()
        fake_stripe.checkout.Session.create.return_value = fake_session

        with patch("ipflow.services.stripe_service._get_stripe_client", return_value=fake_stripe):
            svc = StripeService()
            asyncio.run(svc.create_payment(
                user_id="u1", plan_id="starter", billing_interval="monthly",
                payment_method="stripe", amount=4900, order_no="IPFOO",
                client_ip="127.0.0.1",
            ))

        call_kwargs = fake_stripe.checkout.Session.create.call_args.kwargs
        assert call_kwargs["success_url"].startswith("https://app.example.com/")
        assert "order=IPFOO" in call_kwargs["success_url"]
        assert call_kwargs["cancel_url"].startswith("https://app.example.com/")


# ---------- Webhook 验签 ----------

class TestWebhookVerify:
    """verify_webhook 行为."""

    def test_rejects_when_no_webhook_secret(self, monkeypatch):
        """未配置 STRIPE_WEBHOOK_SECRET 时必须返回 None（拒绝）."""
        monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
        assert StripeService.verify_webhook(b"{}", "t=1,v1=xxx") is None

    def test_rejects_invalid_signature(self, monkeypatch):
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_xxx")
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")

        fake_stripe = MagicMock()
        fake_stripe.Webhook.construct_event.side_effect = ValueError("bad sig")

        with patch("ipflow.services.stripe_service._get_stripe_client", return_value=fake_stripe):
            assert StripeService.verify_webhook(b"{}", "t=1,v1=bad") is None

    def test_returns_event_on_valid_signature(self, monkeypatch):
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_xxx")
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_xxx")

        event = {"id": "evt_123", "type": "checkout.session.completed", "data": {"object": {}}}
        fake_stripe = MagicMock()
        fake_stripe.Webhook.construct_event.return_value = event

        with patch("ipflow.services.stripe_service._get_stripe_client", return_value=fake_stripe):
            result = StripeService.verify_webhook(b"payload", "t=1,v1=good")
        assert result == event


class TestExtractEventInfo:
    """extract_event_info 字段映射."""

    def test_checkout_completed(self):
        event: dict[str, Any] = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_1",
                    "client_reference_id": "IPFORDER123",
                    "subscription": "sub_ABC",
                    "customer": "cus_XYZ",
                    "amount_total": 4900,
                    "currency": "cny",
                }
            },
        }
        info = StripeService.extract_event_info(event)
        assert info["event_type"] == "checkout.session.completed"
        assert info["order_no"] == "IPFORDER123"
        assert info["subscription_id"] == "sub_ABC"
        assert info["customer_id"] == "cus_XYZ"
        assert info["amount_total"] == 4900

    def test_invoice_event(self):
        """invoice.paid 事件应能提取 subscription id."""
        event: dict[str, Any] = {
            "type": "invoice.paid",
            "data": {"object": {"id": "in_1", "subscription": "sub_RENEW"}},
        }
        info = StripeService.extract_event_info(event)
        assert info["event_type"] == "invoice.paid"
        assert info["subscription_id"] == "sub_RENEW"
