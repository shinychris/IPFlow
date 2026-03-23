"""软著 AI 草稿生成服务."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ipflow.models import Project


@dataclass
class DraftResult:
    """草稿生成结果."""

    software_info: dict[str, Any]
    manual: dict[str, Any]


class CopyrightAIGenerator:
    """根据项目信息生成软著草稿内容.

    当前实现先提供稳定的模板化草稿，后续可无缝替换为真实 LLM 流水线。
    """

    def generate(self, project: Project, inputs: dict[str, Any] | None = None) -> DraftResult:
        """生成软件信息与说明书草稿."""
        payload = inputs or {}
        extra_brief = (payload.get("extra_brief") or "").strip()

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
