"""专利 AI 草稿生成服务（默认模板入口，兼容旧引用）."""

from __future__ import annotations

from typing import Any

from ipflow.models import Project
from ipflow.services.patents.draft_providers import (
    PatentDraftResult,
    TemplatePatentDraftProvider,
)


class PatentAIGenerator:
    """根据项目信息生成专利草稿（模板，不调用 Claude Code）."""

    def __init__(self) -> None:
        self._inner = TemplatePatentDraftProvider()

    def generate(self, project: Project, inputs: dict[str, Any] | None = None) -> PatentDraftResult:
        return self._inner.generate(project, inputs or {}, code_root=None)


__all__ = ["PatentAIGenerator", "PatentDraftResult"]
