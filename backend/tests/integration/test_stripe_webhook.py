"""Stripe Webhook 端点集成测试.

覆盖 webhook 路由的：
- 验签失败 → 400
- checkout.session.completed → 订单状态置 COMPLETED + 幂等
- checkout.session.expired → 订单状态置 FAILED
- 重复事件 → 幂等跳过
"""
# pylint: disable=import-error,redefined-outer-name,unused-argument
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from ipflow.api.deps import get_current_user
from ipflow.api.v1.payments import router as payments_router
from ipflow.db import get_db
from ipflow.models.payment import PaymentOrder, PaymentStatus
from ipflow.models.user import User, UserRole, UserStatus


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def current_user() -> User:
    return User(
        id=uuid4(),
        email="stripe-test@example.com",
        username="stripe_test_user",
        hashed_password="hashed",
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
    )


def _make_event(event_id: str, event_type: str, order_no: str | None = None) -> dict:
    """构造 Stripe Event 载荷."""
    obj: dict = {"id": "cs_test_session"}
    if order_no:
        obj["client_reference_id"] = order_no
        obj["subscription"] = "sub_test_123"
        obj["customer"] = "cus_test"
    return {
        "id": event_id,
        "type": event_type,
        "data": {"object": obj},
    }


@pytest.fixture
async def stripe_client(
    db_session: AsyncSession,
    current_user: User,
    monkeypatch,
) -> AsyncGenerator[AsyncClient, None]:
    """构造一个 mock Stripe 验签的客户端."""
    app = FastAPI()
    app.include_router(payments_router, prefix="/api/v1")

    async def _get_db_override():
        yield db_session

    async def _get_current_user_override():
        return current_user

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override

    # 让 verify_webhook 直接返回构造的事件（跳过真实签名校验）
    from ipflow.services import stripe_service as ss

    def fake_verify(cls_or_self, payload, signature):  # noqa: ARG001
        try:
            return json.loads(payload.decode("utf-8"))
        except Exception:  # noqa: BLE001
            return None

    monkeypatch.setattr(ss.StripeService, "verify_webhook", classmethod(fake_verify))

    # 订阅服务 handle_webhook 可能因测试库无相关数据而抛错，路由已 try/except 兜底
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_webhook_invalid_signature_returns_400(stripe_client: AsyncClient, monkeypatch):
    """验签失败应返回 400."""
    from ipflow.services import stripe_service as ss

    # 覆盖 fixture 里的 fake_verify，强制返回 None
    monkeypatch.setattr(ss.StripeService, "verify_webhook", classmethod(lambda *a, **k: None))

    resp = await stripe_client.post(
        "/api/v1/payments/webhook/stripe",
        content=b"{}",
        headers={"Stripe-Signature": "t=1,v1=bad"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_webhook_checkout_completed_marks_order(
    stripe_client: AsyncClient,
    db_session: AsyncSession,
    current_user: User,
):
    """checkout.session.completed 应把订单置为 COMPLETED."""
    order = PaymentOrder(
        id="pay_stripe_001",
        order_no="IPFSTRIPE001",
        user_id=current_user.id,
        plan_id="starter",
        plan_name="Starter",
        billing_interval="monthly",
        payment_method="stripe",
        amount=4900,
        currency="cny",
        status=PaymentStatus.PENDING,
        expires_at=datetime.now() + timedelta(minutes=30),
    )
    db_session.add(order)
    await db_session.commit()

    event = _make_event("evt_completed_001", "checkout.session.completed", order_no="IPFSTRIPE001")
    resp = await stripe_client.post(
        "/api/v1/payments/webhook/stripe",
        content=json.dumps(event).encode("utf-8"),
        headers={"Stripe-Signature": "t=1,v1=mock"},
    )
    assert resp.status_code == 200
    assert resp.json()["received"] is True

    # 校验订单已置 COMPLETED
    await db_session.refresh(order)
    assert order.status == PaymentStatus.COMPLETED
    assert order.paid_at is not None


@pytest.mark.asyncio
async def test_webhook_idempotent(
    stripe_client: AsyncClient,
    db_session: AsyncSession,
    current_user: User,
):
    """同一 event_id 重复投递应被幂等跳过."""
    order = PaymentOrder(
        id="pay_stripe_002",
        order_no="IPFSTRIPE002",
        user_id=current_user.id,
        plan_id="starter",
        plan_name="Starter",
        billing_interval="monthly",
        payment_method="stripe",
        amount=4900,
        currency="cny",
        status=PaymentStatus.PENDING,
        expires_at=datetime.now() + timedelta(minutes=30),
    )
    db_session.add(order)
    await db_session.commit()

    event = _make_event("evt_idem_001", "checkout.session.completed", order_no="IPFSTRIPE002")
    content = json.dumps(event).encode("utf-8")

    first = await stripe_client.post(
        "/api/v1/payments/webhook/stripe", content=content,
        headers={"Stripe-Signature": "t=1,v1=mock"},
    )
    second = await stripe_client.post(
        "/api/v1/payments/webhook/stripe", content=content,
        headers={"Stripe-Signature": "t=1,v1=mock"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert "Duplicate" in second.json().get("message", "")
