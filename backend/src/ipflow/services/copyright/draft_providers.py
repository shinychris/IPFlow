"""软著草稿生成：模板实现与 Claude Code CLI 实现."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ipflow.config import Settings, get_settings
from ipflow.models import Project


@dataclass
class DraftResult:
    """草稿生成结果."""

    software_info: dict[str, Any]
    manual: dict[str, Any]


class TemplateCopyrightDraftProvider:
    """模板化草稿（默认，不调用外部 CLI）."""

    def generate(
        self,
        project: Project,
        inputs: dict[str, Any],
        *,
        code_root: Any | None = None,
    ) -> DraftResult:
        payload = inputs or {}
        inner = payload.get("inputs") or {}
        extra_brief = (inner.get("extra_brief") or "").strip()

        software_name = project.name
        version = project.version or "1.0"

        functional_description = (
            extra_brief
            if extra_brief
            else f"{software_name}用于支撑业务流程管理与信息处理，提供核心业务能力。"
        )
        technical_features = (
            f"系统采用模块化架构，支持权限控制、数据检索与流程追踪；"
            f"版本 {version} 聚焦稳定性与可维护性。"
        )

        software_info = {
            "software_full_name": software_name,
            "software_short_name": software_name[:20],
            "version_number": version,
            "development_language": "Python/TypeScript",
            "development_environment": "Linux/macOS, Node.js, Python",
            "runtime_environment": "Web 浏览器 + 服务端 API",
            "code_line_count": None,
            "functional_description": functional_description,
            "technical_features": technical_features,
            "target_domain": "企业信息化",
            "source": "ai",
        }

        manual_html = (
            f"<h1>{software_name} 操作说明书（草稿）</h1>"
            "<h2>1. 产品概述</h2>"
            f"<p>{functional_description}</p>"
            "<h2>2. 功能模块</h2>"
            "<p>系统包含账号权限、项目管理、材料生成与导出等模块。</p>"
            "<h2>3. 基本操作流程</h2>"
            "<ol>"
            "<li>创建项目并完善基础信息</li>"
            "<li>检查 AI 生成草稿并编辑修订</li>"
            "<li>执行合规检查并导出材料包</li>"
            "</ol>"
        )

        manual = {
            "template_type": "web",
            "title": f"{software_name} 操作说明书",
            "content_html": manual_html,
            "content_json": None,
            "source": "ai",
        }

        return DraftResult(software_info=software_info, manual=manual)


class ClaudeCodeCopyrightDraftProvider:
    """通过 Claude Code headless 与 JSON Schema 结构化输出生成草稿."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def generate(
        self,
        project: Project,
        inputs: dict[str, Any],
        *,
        code_root: Any | None = None,
    ) -> DraftResult:
        from ipflow.services.copyright.claude_code_runner import run_copyright_claude_draft

        return run_copyright_claude_draft(
            project,
            inputs,
            code_root=code_root,
            settings=self._settings,
        )


def get_copyright_draft_provider(
    settings: Settings | None = None,
) -> TemplateCopyrightDraftProvider | ClaudeCodeCopyrightDraftProvider:
    cfg = settings or get_settings()
    if cfg.COPYRIGHT_DRAFT_BACKEND.strip().lower() == "claude_code":
        return ClaudeCodeCopyrightDraftProvider(cfg)
    return TemplateCopyrightDraftProvider()
