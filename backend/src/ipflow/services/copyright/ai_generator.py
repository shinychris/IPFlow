"""软著 AI 草稿生成服务（模板实现入口，兼容旧代码路径）."""

from __future__ import annotations

from typing import Any

from ipflow.models import Project
from ipflow.services.copyright.draft_providers import (
    DraftResult,
    TemplateCopyrightDraftProvider,
)


class CopyrightAIGenerator:
    """根据项目信息生成软著草稿内容（默认模板，不调用 Claude Code）."""

    def __init__(self) -> None:
        self._inner = TemplateCopyrightDraftProvider()

    def generate(self, project: Project, inputs: dict[str, Any] | None = None) -> DraftResult:
        """生成软件信息与说明书草稿."""
        return self._inner.generate(project, inputs or {}, code_root=None)


__all__ = ["CopyrightAIGenerator", "DraftResult"]
