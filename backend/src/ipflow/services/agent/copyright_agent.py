"""软著草稿 Agent 后端（pydantic-ai + 软著申请技能 SKILL.md）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from ipflow.config import Settings, get_settings
from ipflow.services.agent.base import BaseAgentDraftProvider


class CopyrightSoftwareInfo(BaseModel):
    """软著软件信息（与 copyright_draft_output.schema.json 对齐）。"""

    software_full_name: str = Field("", description="软件全称")
    software_short_name: str = Field("", description="软件简称")
    version_number: str = Field("", description="版本号")
    development_language: str = Field("", description="开发语言")
    development_environment: str = Field("", description="开发环境")
    runtime_environment: str = Field("", description="运行环境")
    functional_description: str = Field("", description="功能描述")
    technical_features: str = Field("", description="技术特点")
    target_domain: str = Field("", description="面向领域")
    source: str = Field("ai", description="来源标记")


class CopyrightManual(BaseModel):
    """软著操作说明书。"""

    template_type: str = Field("web", description="说明书模板类型")
    title: str = Field("", description="说明书标题")
    content_html: str = Field("", description="HTML 正文")
    content_json: Optional[Any] = Field(None, description="结构化正文（可选）")
    source: str = Field("ai", description="来源标记")


class CopyrightDraftOutput(BaseModel):
    """软著草稿结构化输出。"""

    software_info: CopyrightSoftwareInfo
    manual: CopyrightManual


class CopyrightAgentDraftProvider(BaseAgentDraftProvider[CopyrightDraftOutput]):
    """软著草稿 Agent 后端。"""

    output_model = CopyrightDraftOutput
    instructions_prefix = (
        "你是软件著作权申报材料撰写助手。请根据用户提供的软件信息，"
        "严格按结构化输出格式生成「软件基本信息」与「操作说明书」。"
        "严格遵循下方技能（SKILL）的规范要求。"
    )

    def get_skill_path(self) -> Path:
        from ipflow.config import get_settings

        cfg = self._settings or get_settings()
        return cfg.resolve_backend_path(cfg.CLAUDE_CODE_SKILL_PROMPT_FILE)

    def build_user_prompt(self, project: Any, inputs: dict[str, Any]) -> str:
        payload = inputs or {}
        inner = payload.get("inputs") or {}
        extra_brief = (inner.get("extra_brief") or "").strip()
        name = getattr(project, "name", "未命名软件")
        version = getattr(project, "version", "1.0")
        return (
            f"请为以下软件生成软著申请草稿材料。\n\n"
            f"软件名称：{name}\n版本：{version}\n"
            f"补充说明：{extra_brief or '（无）'}\n\n"
            f"请输出 software_info 与 manual 两个字段。manual.content_html 为完整 HTML 正文，"
            f"包含产品概述、功能模块、操作流程等章节。"
        )

    def to_draft_result(self, output: CopyrightDraftOutput, project: Any) -> Any:
        from ipflow.services.copyright.draft_providers import DraftResult

        software_info = output.software_info.model_dump()
        manual = output.manual.model_dump()
        # 确保来源标记为 ai
        software_info["source"] = "ai"
        manual["source"] = "ai"
        return DraftResult(software_info=software_info, manual=manual)
