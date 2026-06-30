"""邮箱验证与密码重置流程测试（P1-C / P1-D）.

覆盖：
- 动作令牌签发与校验（用途隔离、过期、无效）
- 邮箱验证端点
- 密码重置端点
- 防枚举：不存在的邮箱也返回成功
"""
# pylint: disable=import-error,redefined-outer-name,unused-argument
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from uuid import uuid4

import jwt
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from ipflow.api.deps import get_current_user
from ipflow.api.v1.auth import router as auth_router
from ipflow.config import get_settings
from ipflow.core import action_token as at
from ipflow.core.security import verify_password
from ipflow.db import get_db
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
async def client(db_session: AsyncSession, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    """构造测试客户端，禁用限流计数污染."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    # 注册全局异常处理器，使 ValidationException 等返回标准错误响应而非向上抛
    from ipflow.core.exceptions import setup_exception_handlers
    setup_exception_handlers(app)

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override

    # 重置 limiter 内存存储，避免跨测试累积触发限流
    from ipflow.core.rate_limit import limiter
    limiter.reset()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def _create_user(db: AsyncSession, email: str = "verify@example.com") -> User:
    """创建测试用户."""
    from ipflow.core.security import get_password_hash
    user = User(
        id=uuid4(),
        email=email,
        username=email.split("@")[0],
        hashed_password=get_password_hash("OldPass123"),
        role=UserRole.MEMBER,
        status=UserStatus.ACTIVE,
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ---------- 动作令牌单元测试 ----------

class TestActionToken:
    """动作令牌签发与校验."""

    def test_sign_and_verify_email(self):
        t = at.create_action_token("u1", at.PURPOSE_EMAIL_VERIFICATION)
        r = at.verify_action_token(t, at.PURPOSE_EMAIL_VERIFICATION)
        assert r.is_valid
        assert r.user_id == "u1"

    def test_purpose_isolation(self):
        """邮箱验证令牌不可用于密码重置."""
        t = at.create_action_token("u1", at.PURPOSE_EMAIL_VERIFICATION)
        r = at.verify_action_token(t, at.PURPOSE_PASSWORD_RESET)
        assert not r.is_valid
        assert "用途不匹配" in (r.error or "")

    def test_expired_token(self):
        """过期令牌应被拒绝."""
        settings = get_settings()
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "u1",
            "purpose": at.PURPOSE_PASSWORD_RESET,
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),  # 已过期
        }
        expired = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        r = at.verify_action_token(expired, at.PURPOSE_PASSWORD_RESET)
        assert not r.is_valid
        assert "过期" in (r.error or "")

    def test_invalid_token(self):
        r = at.verify_action_token("not-a-jwt", at.PURPOSE_EMAIL_VERIFICATION)
        assert not r.is_valid


# ---------- 端点集成测试 ----------

@pytest.mark.asyncio
async def test_verify_email_success(client: AsyncClient, db_session: AsyncSession):
    """有效令牌应将用户标记为已验证."""
    user = await _create_user(db_session)
    token = at.create_action_token(str(user.id), at.PURPOSE_EMAIL_VERIFICATION)

    resp = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200

    await db_session.refresh(user)
    assert user.is_verified is True


@pytest.mark.asyncio
async def test_verify_email_invalid_token(client: AsyncClient):
    """无效令牌应返回 422."""
    resp = await client.post("/api/v1/auth/verify-email", json={"token": "bad"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_verify_email_idempotent(client: AsyncClient, db_session: AsyncSession):
    """已验证用户再次验证应返回成功（幂等）."""
    user = await _create_user(db_session)
    user.is_verified = True
    await db_session.commit()
    token = at.create_action_token(str(user.id), at.PURPOSE_EMAIL_VERIFICATION)

    resp = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_no_enumeration(client: AsyncClient):
    """不存在的邮箱也应返回成功（防枚举）."""
    resp = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert resp.status_code == 200
    assert "已发送" in resp.json()["message"] or "success" in resp.json().get("code", "").lower()


@pytest.mark.asyncio
async def test_reset_password_success(client: AsyncClient, db_session: AsyncSession):
    """有效重置令牌应更新密码."""
    user = await _create_user(db_session)
    old_hash = user.hashed_password
    token = at.create_action_token(str(user.id), at.PURPOSE_PASSWORD_RESET)

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewPass456"},
    )
    assert resp.status_code == 200

    await db_session.refresh(user)
    assert user.hashed_password != old_hash
    assert verify_password("NewPass456", user.hashed_password)
    # 旧密码应失效
    assert not verify_password("OldPass123", user.hashed_password)


@pytest.mark.asyncio
async def test_reset_password_weak_password_rejected(client: AsyncClient, db_session: AsyncSession):
    """弱密码应被拒绝."""
    user = await _create_user(db_session)
    token = at.create_action_token(str(user.id), at.PURPOSE_PASSWORD_RESET)

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "123"},  # 太短
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_wrong_purpose_token(client: AsyncClient, db_session: AsyncSession):
    """邮箱验证令牌不可用于重置密码."""
    user = await _create_user(db_session)
    token = at.create_action_token(str(user.id), at.PURPOSE_EMAIL_VERIFICATION)

    resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewPass456"},
    )
    # 用途不匹配应返回 422
    assert resp.status_code == 422
