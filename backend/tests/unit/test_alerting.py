"""告警模块单元测试（P1 监控告警）.

覆盖：
- 监控初始化（无 DSN 降级）
- capture_exception / capture_message（无 Sentry 时降级日志）
- send_alert（无 Webhook 返回 False；info 级别不推送）
"""
# pylint: disable=import-error,redefined-outer-name,unused-argument
from __future__ import annotations

import asyncio

import pytest

from ipflow.core import alerting


class TestInitMonitoring:
    """监控初始化."""

    def test_init_idempotent(self, monkeypatch):
        """重复初始化只生效一次."""
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        alerting._sentry_initialized = False  # 重置单例状态
        alerting.init_monitoring()
        assert alerting._sentry_initialized is True
        # 再次调用不应报错
        alerting.init_monitoring()


class TestCapture:
    """异常/消息捕获（无 Sentry 时降级日志，不抛错）."""

    def test_capture_exception_no_dsn(self, monkeypatch):
        """无 DSN 时捕获异常应安全降级（仅日志）."""
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        # 不应抛异常
        alerting.capture_exception(ValueError("test error"), path="/api/x")

    def test_capture_message_no_dsn(self, monkeypatch):
        """无 DSN 时捕获消息应安全降级."""
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        alerting.capture_message("test msg", level="warning", user="u1")

    def test_capture_exception_with_fake_dsn(self, monkeypatch):
        """有 DSN 但 sentry-sdk 初始化失败时应降级（不阻断）."""
        monkeypatch.setenv("SENTRY_DSN", "https://fake@example.com/1")
        # 即使初始化逻辑跑，capture 也应安全
        alerting._sentry_initialized = True
        alerting.capture_exception(RuntimeError("boom"))


class TestSendAlert:
    """告警 Webhook 推送."""

    @pytest.mark.asyncio
    async def test_no_webhook_returns_false(self, monkeypatch):
        """未配置 ALERT_WEBHOOK_URL 时应返回 False."""
        monkeypatch.delenv("ALERT_WEBHOOK_URL", raising=False)
        alerting._alert_webhook_url = None
        result = await alerting.send_alert("title", "detail", level="error")
        assert result is False

    @pytest.mark.asyncio
    async def test_info_level_not_pushed(self, monkeypatch):
        """info 级别不应推送（避免噪音）."""
        alerting._alert_webhook_url = "http://fake.example.com/hook"
        result = await alerting.send_alert("title", "detail", level="info")
        assert result is False

    @pytest.mark.asyncio
    async def test_push_failure_safe(self, monkeypatch):
        """推送失败应安全降级返回 False，不抛异常."""
        alerting._alert_webhook_url = "http://invalid.invalid/hook"
        result = await alerting.send_alert("title", "detail", level="error")
        # 连接失败应返回 False
        assert result is False
