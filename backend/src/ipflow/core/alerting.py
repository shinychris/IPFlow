"""错误监控与告警.

采用「Sentry 优先，降级日志/Webhook」策略：

- **SENTRY_DSN 已配置**：通过 ``sentry-sdk`` 自动捕获未处理异常、记录上下文。
- **SENTRY_DSN 未配置**：错误降级到结构化日志，并通过可选的告警 Webhook
  （``ALERT_WEBHOOK_URL``）推送关键错误，便于接入飞书/钉钉/企业微信机器人。

设计要点：
- 单例初始化，整个进程只配置一次 Sentry。
- 暴露 ``capture_exception`` / ``capture_message`` 供业务代码主动上报。
- 告警 Webhook 按错误级别过滤（默认仅 ERROR/CRITICAL），避免噪音。
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

_sentry_initialized = False
_alert_webhook_url: Optional[str] = None


def init_monitoring() -> None:
    """初始化监控（应在应用启动时调用一次）.

    读取环境变量：
    - ``SENTRY_DSN``：配置则启用 Sentry
    - ``SENTRY_ENVIRONMENT``：环境标识（production/staging）
    - ``SENTRY_TRACES_SAMPLE_RATE``：性能采样率（0.0-1.0）
    - ``ALERT_WEBHOOK_URL``：告警 Webhook（飞书/钉钉等）
    """
    global _sentry_initialized, _alert_webhook_url

    if _sentry_initialized:
        return

    dsn = os.environ.get("SENTRY_DSN")
    _alert_webhook_url = os.environ.get("ALERT_WEBHOOK_URL")

    if dsn:
        try:
            import sentry_sdk  # type: ignore[import-untyped]
            from sentry_sdk.integrations.asyncio import AsyncioIntegration  # noqa: F401

            sentry_sdk.init(
                dsn=dsn,
                environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
                traces_sample_rate=float(
                    os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")
                ),
                send_default_pii=False,  # 不收集 PII，符合隐私合规
                max_breadcrumbs=50,
            )
            logger.info("Sentry 监控已启用（env=%s）", os.environ.get("SENTRY_ENVIRONMENT"))
        except ImportError:
            logger.warning("sentry-sdk 未安装，错误监控降级到日志")
        except Exception as e:  # noqa: BLE001 监控初始化失败不应阻断启动
            logger.warning("Sentry 初始化失败，降级到日志：%s", e)

    _sentry_initialized = True


def capture_exception(exc: BaseException, **context: Any) -> None:
    """主动上报异常.

    Args:
        exc: 异常对象
        **context: 额外上下文（tag/extra）
    """
    # Sentry 上报
    try:
        if _sentry_initialized and os.environ.get("SENTRY_DSN"):
            import sentry_sdk  # type: ignore[import-untyped]

            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, value)
                sentry_sdk.capture_exception(exc)
    except Exception as e:  # noqa: BLE001
        logger.debug("Sentry 上报失败：%s", e)

    # 本地日志（始终记录）
    logger.error("捕获异常：%s: %s | context=%s", type(exc).__name__, exc, context)


def capture_message(message: str, level: str = "info", **context: Any) -> None:
    """主动上报消息.

    Args:
        message: 消息内容
        level: 级别（info/warning/error）
        **context: 额外上下文
    """
    try:
        if _sentry_initialized and os.environ.get("SENTRY_DSN"):
            import sentry_sdk  # type: ignore[import-untyped]

            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, value)
                sentry_sdk.capture_message(message, level=level)
    except Exception as e:  # noqa: BLE001
        logger.debug("Sentry 消息上报失败：%s", e)

    log_method = {
        "debug": logger.debug,
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error,
    }.get(level, logger.info)
    log_method("监控消息[%s]：%s | context=%s", level, message, context)


async def send_alert(
    title: str,
    detail: str,
    level: str = "error",
) -> bool:
    """通过告警 Webhook 推送通知（飞书/钉钉/企业微信等）.

    仅当配置了 ``ALERT_WEBHOOK_URL`` 时生效；推送失败仅记录日志，不抛异常。

    Args:
        title: 告警标题
        detail: 告警详情
        level: 级别（error/warning/info）

    Returns:
        是否推送成功（未配置 Webhook 返回 False）
    """
    if not _alert_webhook_url:
        return False

    # error/warning 才推送，info 仅日志，避免噪音
    if level == "info":
        logger.info("告警[info]：%s - %s", title, detail)
        return False

    payload = {
        "title": f"[{level.upper()}] {title}",
        "text": f"{title}\n{detail}",
        # 兼容飞书/钉钉/企业微信的通用字段
        "msg_type": "text",
        "content": {"text": f"[{level.upper()}] {title}\n{detail}"},
    }

    try:
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(_alert_webhook_url, json=payload)
            if resp.status_code < 300:
                logger.info("告警已推送：%s", title)
                return True
            logger.warning("告警推送失败 HTTP %s：%s", resp.status_code, resp.text[:200])
    except Exception as e:  # noqa: BLE001
        logger.warning("告警推送异常：%s", e)
    return False
