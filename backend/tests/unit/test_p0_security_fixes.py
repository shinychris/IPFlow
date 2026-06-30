"""P0 安全整改验证测试.

覆盖：
- CORS 配置解析（白名单/开发兜底/生产空）
- TenantMiddleware 注册与上下文注入
"""
# pylint: disable=import-error,redefined-outer-name,unused-argument
from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ipflow.config import Settings
from ipflow.core.tenant import TenantContext, TenantMiddleware


class TestCorsConfig:
    """CORS_ALLOWED_ORIGINS 解析（修复 P0-4 矛盾配置）."""

    def test_prod_with_whitelist(self, monkeypatch):
        """生产环境配置白名单时应返回明确的域名列表."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.ipflow.com,https://www.ipflow.com")
        s = Settings()
        assert s.cors_allowed_origins_list == [
            "https://app.ipflow.com",
            "https://www.ipflow.com",
        ]

    def test_prod_empty_returns_empty(self, monkeypatch):
        """生产环境未配置白名单时返回空列表（不回退到 *，安全默认）."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
        s = Settings()
        assert s.cors_allowed_origins_list == []

    def test_dev_empty_fallback_localhost(self, monkeypatch):
        """开发环境未配置时回退到 localhost:3000."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
        s = Settings()
        assert "http://localhost:3000" in s.cors_allowed_origins_list

    def test_trailing_slash_stripped(self, monkeypatch):
        """白名单域名末尾斜杠应被去除，避免 CORS 匹配失败."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.ipflow.com/")
        s = Settings()
        assert s.cors_allowed_origins_list == ["https://app.ipflow.com"]


class TestTenantMiddleware:
    """TenantMiddleware 注册与上下文注入（修复 P0-3）."""

    def test_registered_in_main_app(self):
        """main.py 应已注册 TenantMiddleware."""
        from ipflow.main import app

        mw_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "TenantMiddleware" in mw_classes

    @pytest.mark.asyncio
    async def test_sets_context_from_header(self):
        """带 x-tenant-id 请求头时，下游应能读到租户上下文."""
        captured: dict = {}

        async def downstream(scope, receive, send):  # noqa: ARG001
            captured["tenant_id"] = TenantContext.get_current_tenant_id()
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        app = TenantMiddleware(downstream)
        tenant = uuid4()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/", headers={"x-tenant-id": str(tenant)})

        assert resp.status_code == 200
        assert captured["tenant_id"] == tenant

    @pytest.mark.asyncio
    async def test_clears_context_after_request(self):
        """请求结束后上下文应被清理，避免跨请求泄漏."""
        async def downstream(scope, receive, send):  # noqa: ARG001
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        app = TenantMiddleware(downstream)
        tenant = uuid4()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.get("/", headers={"x-tenant-id": str(tenant)})

        # 请求结束后上下文应已清理
        assert TenantContext.get_current_tenant_id() is None

    @pytest.mark.asyncio
    async def test_invalid_tenant_header_ignored(self):
        """无效的 x-tenant-id 应被静默忽略，不影响请求处理."""
        async def downstream(scope, receive, send):  # noqa: ARG001
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        app = TenantMiddleware(downstream)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/", headers={"x-tenant-id": "not-a-uuid"})

        assert resp.status_code == 200
        assert resp.content == b"ok"


class TestEnvNotTracked:
    """P0-2: backend/.env 不应被 git 跟踪."""

    def test_backend_env_ignored_by_git(self):
        """backend/.env 应被 .gitignore 忽略."""
        import subprocess

        result = subprocess.run(
            ["git", "check-ignore", "backend/.env"],
            capture_output=True, text=True, cwd=os.getcwd(),
        )
        # check-ignore 返回 0 表示该文件被忽略
        assert result.returncode == 0, f"backend/.env 未被忽略: {result.stderr}"
        assert "backend/.env" in result.stdout
