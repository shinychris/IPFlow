"""商标 AI 草稿生成服务（默认模板入口，兼容旧引用）."""

from __future__ import annotations

from typing import Any

from ipflow.models import Project
from ipflow.services.trademarks.draft_providers import (
    TemplateTrademarkDraftProvider,
    TrademarkDraftResult,
)


class TrademarkAIGenerator:
    """根据项目信息生成商标草稿（模板，不调用 Claude Code）."""

    def __init__(self) -> None:
        self._inner = TemplateTrademarkDraftProvider()

    def generate(self, project: Project, inputs: dict[str, Any] | None = None) -> TrademarkDraftResult:
        return self._inner.generate(project, inputs or {}, code_root=None)


__all__ = ["TrademarkAIGenerator", "TrademarkDraftResult"]
