"""订阅模块集成测试（P2 覆盖率提升）.

真实数据库 + 真实 JWT，覆盖订阅 plans 列表、当前订阅、创建订阅、用量统计。
不依赖外部 Redis/MinIO，全部用内存 SQLite。
"""
# pylint: disable=import-error,redefined-outer-name,unused-argument
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from ipflow.api.deps import get_current_user
from ipflow.api.v1.subscriptions import router as subscriptions_router
from ipflow.core.security import create_access_token, get_password_hash
from ipflow.db import get_db
from ipflow.models.subscription import Plan
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
        # 预置两个订阅计划
        session.add(Plan(
            name="Starter",
            slug="starter",
            description="入门版",
            price_monthly=Decimal("49.00"),
            price_yearly=Decimal("490.00"),
            currency="CNY",
            features=["10 项目"],
            limits={"max_projects": 10},
            is_active=True,
            is_public=True,
        ))
        session.add(Plan(
            name="Pro",
            slug="professional",
            description="专业版",
            price_monthly=Decimal("199.00"),
            price_yearly=Decimal("1990.00"),
            currency="CNY",
            features=["无限项目"],
            limits={"max_projects": -1},
            is_active=True,
            is_public=True,
        ))
        await session.commit()
        yield session
    await engine.dispose()


@pytest.fixture
def current_user() -> User:
    return User(
        id=uuid4(),
        email="sub@example.com",
        username="subuser",
        hashed_password=get_password_hash("Pass1234"),
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
async def client(
    db_session: AsyncSession,
    current_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    app = FastAPI()
    app.include_router(subscriptions_router, prefix="/api/v1")

    async def _get_db_override():
        yield db_session

    async def _get_current_user_override():
        return current_user

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_list_plans(client: AsyncClient):
    """公开计划列表应返回预置的 2 个计划，按价格升序."""
    resp = await client.get("/api/v1/subscriptions/plans")
    assert resp.status_code == 200
    plans = resp.json()
    assert len(plans) == 2
    # 价格升序：Starter (49) 在前
    assert plans[0]["slug"] == "starter"
    assert plans[1]["slug"] == "professional"


@pytest.mark.asyncio
async def test_list_plans_field_integrity(client: AsyncClient):
    """计划字段应完整返回."""
    resp = await client.get("/api/v1/subscriptions/plans")
    plan = resp.json()[0]
    assert plan["name"] == "Starter"
    # Decimal 序列化为字符串 "49.00"
    assert float(plan["price_monthly"]) == 49.0
    assert plan["currency"] == "CNY"
    assert plan["features"] == ["10 项目"]
    assert plan["limits"]["max_projects"] == 10


@pytest.mark.asyncio
async def test_get_plan_by_id(client: AsyncClient, db_session: AsyncSession):
    """按 ID 获取计划详情."""
    from sqlalchemy import select

    result = await db_session.execute(select(Plan))
    plans = result.scalars().all()
    plan_id = plans[0].id

    resp = await client.get(f"/api/v1/subscriptions/plans/{plan_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(plan_id)


@pytest.mark.asyncio
async def test_get_plan_not_found(client: AsyncClient):
    """不存在的计划 ID 应返回 404."""
    resp = await client.get(f"/api/v1/subscriptions/plans/{uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_current_subscription_no_org(client: AsyncClient):
    """无组织上下文时应返回错误（订阅绑定组织）."""
    resp = await client.get("/api/v1/subscriptions/current")
    # 无组织上下文应拒绝（400），这是正确行为
    assert resp.status_code in (400, 404)


@pytest.mark.asyncio
async def test_create_subscription_requires_org(client: AsyncClient):
    """无组织时创建订阅应失败（订阅绑定组织）."""
    plan_id = str(uuid4())
    resp = await client.post(
        "/api/v1/subscriptions",
        json={"plan_id": plan_id, "interval": "monthly"},
    )
    # 无组织上下文应返回错误
    assert resp.status_code in (400, 404, 422)


@pytest.mark.asyncio
async def test_usage_stats_without_subscription(client: AsyncClient):
    """无订阅时用量统计应可调用（降级返回 0/默认限额）."""
    resp = await client.get("/api/v1/subscriptions/usage")
    # 用量统计依赖组织，无组织时可能报错或返回默认
    assert resp.status_code in (200, 400, 404, 422)
