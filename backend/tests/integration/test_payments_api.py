"""支付 API 集成测试（mock/sandbox 链路）."""
# pylint: disable=import-error,redefined-outer-name,unused-argument

from datetime import datetime, timedelta
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from ipflow.api.deps import get_current_user
from ipflow.api.v1.payments import router as payments_router
from ipflow.db import get_db
from ipflow.models.payment import PaymentOrder, PaymentStatus
from ipflow.models.user import User, UserRole, UserStatus


class _MockPaymentService:
    def generate_order_no(self) -> str:
        return "IPFTEST202603160001"

    async def create_payment(self, **_kwargs) -> dict:
        return {
            "qr_code": "weixin://mock_qr",
            "pay_url": "https://mock.alipay/pay",
        }

    async def verify_payment(self, _payment_id: str, _data: dict) -> bool:
        return True


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
        email="payment-test@example.com",
        username="payment_test_user",
        hashed_password="hashed",
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
async def payment_client(db_session: AsyncSession, current_user: User, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    app = FastAPI()
    app.include_router(payments_router, prefix="/api/v1")

    async def _get_db_override():
        yield db_session

    async def _get_current_user_override():
        return current_user

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override

    from ipflow.services.payment_service import PaymentServiceFactory

    mock_service = _MockPaymentService()
    monkeypatch.setattr(PaymentServiceFactory, "get_service", lambda *_: mock_service)
    monkeypatch.setattr(PaymentServiceFactory, "get_wechat_service", lambda: mock_service)
    monkeypatch.setattr(PaymentServiceFactory, "get_alipay_service", lambda: mock_service)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_payment_success(payment_client: AsyncClient):
    payload = {
        "plan_id": "starter",
        "billing_interval": "yearly",
        "payment_method": "wechat",
    }
    response = await payment_client.post("/api/v1/payments/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["payment_method"] == "wechat"
    assert data["order_no"]


@pytest.mark.asyncio
async def test_get_payment_status_success(payment_client: AsyncClient, db_session: AsyncSession, current_user: User):
    payment_order = PaymentOrder(
        id="pay_status_001",
        order_no="IPFTESTSTATUS001",
        user_id=current_user.id,
        plan_id="starter",
        plan_name="Starter",
        billing_interval="yearly",
        payment_method="wechat",
        amount=49000,
        currency="CNY",
        status=PaymentStatus.PENDING,
        expires_at=datetime.now() + timedelta(minutes=30),
    )
    db_session.add(payment_order)
    await db_session.commit()

    response = await payment_client.get("/api/v1/payments/pay_status_001/status")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_wechat_webhook_idempotent(payment_client: AsyncClient, db_session: AsyncSession, current_user: User):
    payment_order = PaymentOrder(
        id="pay_hook_001",
        order_no="IPFTESTHOOK001",
        user_id=current_user.id,
        plan_id="starter",
        plan_name="Starter",
        billing_interval="yearly",
        payment_method="wechat",
        amount=49000,
        currency="CNY",
        status=PaymentStatus.PENDING,
        expires_at=datetime.now() + timedelta(minutes=30),
    )
    db_session.add(payment_order)
    await db_session.commit()

    payload = {
        "out_trade_no": "IPFTESTHOOK001",
        "trade_state": "SUCCESS",
        "transaction_id": "mock_txn_001",
    }
    first = await payment_client.post("/api/v1/payments/webhook/wechat", json=payload)
    second = await payment_client.post("/api/v1/payments/webhook/wechat", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["message"] == "Duplicate ignored"
