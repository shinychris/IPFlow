"""商标尼斯分类 + 合规检查集成测试（P2 覆盖率提升）.

真实数据库，覆盖尼斯分类查询/筛选/搜索、合规检查（无项目时降级）。
"""
# pylint: disable=import-error,redefined-outer-name,unused-argument
from __future__ import annotations

from typing import AsyncGenerator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from ipflow.api.deps import get_current_user
from ipflow.api.v1.trademarks.nice_classification import router as nice_router
from ipflow.api.v1.compliance import router as compliance_router
from ipflow.db import get_db
from ipflow.models.trademark import NiceClassification
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
        # 预置几个尼斯分类
        for num, name in [(1, "化学原料"), (9, "科学仪器"), (25, "服装鞋帽")]:
            session.add(NiceClassification(
                class_number=num,
                class_name=name,
                class_name_en=f"Class {num}",
                description=f"{name}相关",
                is_active=True,
            ))
        await session.commit()
        yield session
    await engine.dispose()


@pytest.fixture
def current_user() -> User:
    return User(
        id=uuid4(),
        email="nice@example.com",
        username="niceuser",
        hashed_password="hashed",
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
    )


@pytest.fixture
async def nice_client(
    db_session: AsyncSession,
    current_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """尼斯分类测试客户端（路由前缀需匹配 trademarks 的子路由结构）."""
    app = FastAPI()
    from ipflow.api.v1.trademarks import router as trademarks_router
    app.include_router(trademarks_router, prefix="/api/v1")

    async def _get_db_override():
        yield db_session

    async def _get_current_user_override():
        return current_user

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def compliance_client(
    db_session: AsyncSession,
    current_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    app = FastAPI()
    app.include_router(compliance_router, prefix="/api/v1")

    async def _get_db_override():
        yield db_session

    async def _get_current_user_override():
        return current_user

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = _get_current_user_override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------- 尼斯分类 ----------

@pytest.mark.asyncio
async def test_list_nice_classes(nice_client: AsyncClient):
    """无筛选时应返回全部 3 个预置分类."""
    # 尼斯分类为全局端点（不依赖 project_id）
    resp = await nice_client.get("/api/v1/trademarks/nice-classes")
    assert resp.status_code == 200
    data = resp.json()
    # 返回结构可能是 {items: [...]} 或 {data: [...]}
    items = data.get("items") or data.get("data") or data
    assert len(items) == 3


@pytest.mark.asyncio
async def test_filter_nice_class_by_number(nice_client: AsyncClient):
    """按类别号筛选应返回单个分类."""
    resp = await nice_client.get("/api/v1/trademarks/nice-classes?class_number=9")
    assert resp.status_code == 200
    data = resp.json()
    items = data.get("items") or data.get("data") or data
    assert len(items) == 1
    assert items[0]["class_number"] == 9
    assert items[0]["class_name"] == "科学仪器"


@pytest.mark.asyncio
async def test_search_nice_class(nice_client: AsyncClient):
    """关键词搜索应返回匹配分类."""
    resp = await nice_client.get("/api/v1/trademarks/nice-classes?search=化学")
    assert resp.status_code == 200
    data = resp.json()
    items = data.get("items") or data.get("data") or data
    assert len(items) == 1
    assert items[0]["class_number"] == 1


@pytest.mark.asyncio
async def test_get_nice_class_by_id(nice_client: AsyncClient, db_session: AsyncSession):
    """按类别号精确查询应返回详情."""
    # 直接用类别号 1 查询
    resp = await nice_client.get("/api/v1/trademarks/nice-classes?class_number=1")
    assert resp.status_code == 200
    data = resp.json()
    items = data.get("items") or data.get("data") or data
    assert items[0]["class_name"] == "化学原料"


# ---------- 合规检查 ----------

@pytest.mark.asyncio
async def test_compliance_check_project_not_found(compliance_client: AsyncClient):
    """不存在的项目应返回 404."""
    fake_id = str(uuid4())
    resp = await compliance_client.get(f"/api/v1/compliance/projects/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_compliance_check_not_found(compliance_client: AsyncClient):
    """对不存在的项目执行合规检查应返回 404."""
    fake_id = str(uuid4())
    resp = await compliance_client.post(f"/api/v1/compliance/projects/{fake_id}/check")
    assert resp.status_code == 404
