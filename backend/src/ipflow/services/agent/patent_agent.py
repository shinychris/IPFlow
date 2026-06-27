"""专利草稿 Agent 后端（pydantic-ai + 中国专利申请技能 SKILL.md）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from ipflow.config import Settings
from ipflow.services.agent.base import BaseAgentDraftProvider


class PatentInventionContent(BaseModel):
    """发明内容（要解决的技术问题 / 技术方案 / 有益效果）。"""

    problem_solved: str = Field("", description="要解决的技术问题")
    technical_solution: str = Field("", description="技术方案")
    beneficial_effects: str = Field("", description="有益效果")


class PatentInfo(BaseModel):
    patent_type: str = Field("invention", description="专利类型")
    title: str = Field("", description="发明名称")
    technical_field: str = Field("", description="技术领域")
    background_art: str = Field("", description="背景技术")
    abstract: str = Field("", description="摘要")
    abstract_figure_number: Optional[str] = Field(None, description="摘要附图编号")


class PatentClaim(BaseModel):
    claim_number: int = Field(..., description="权利要求编号")
    claim_type: str = Field("independent", description="权利要求类型")
    parent_claim_number: Optional[int] = Field(None, description="从属权利要求的引用项")
    content: str = Field("", description="权利要求内容")


class PatentDescription(BaseModel):
    technical_field: str = Field("", description="技术领域")
    background_art: str = Field("", description="背景技术")
    invention_content: PatentInventionContent
    implementation: str = Field("", description="具体实施方式")


class PatentDraftOutput(BaseModel):
    """专利草稿结构化输出（与 patent_draft_output.schema.json 对齐）。"""

    patent_info: PatentInfo
    claims: list[PatentClaim]
    description: PatentDescription


class PatentAgentDraftProvider(BaseAgentDraftProvider[PatentDraftOutput]):
    """专利草稿 Agent 后端。"""

    output_model = PatentDraftOutput
    instructions_prefix = (
        "你是中国专利申请材料撰写助手。请根据用户提供的信息，"
        "严格按结构化输出格式生成专利「基本信息」「权利要求」与「说明书」。"
        "严格遵循下方技能（SKILL）的规范要求。"
    )

    def get_skill_path(self) -> Path:
        cfg = self._settings
        return cfg.resolve_backend_path(cfg.CLAUDE_CODE_PATENT_SKILL_PROMPT_FILE)

    def build_user_prompt(self, project: Any, inputs: dict[str, Any]) -> str:
        payload = inputs or {}
        inner = payload.get("inputs") or {}
        title = inner.get("title") or getattr(project, "name", "未命名发明")
        ptype = inner.get("patent_type", "invention")
        brief = (inner.get("abstract") or inner.get("extra_brief") or "").strip()
        return (
            f"请为以下发明生成专利申请草稿材料。\n\n"
            f"发明名称：{title}\n专利类型：{ptype}\n"
            f"技术简介：{brief or '（无，请据此合理生成）'}\n\n"
            f"请输出 patent_info、claims（至少 1 项独立权利要求）、description 三个字段。"
        )

    def to_draft_result(self, output: PatentDraftOutput, project: Any) -> Any:
        from ipflow.services.patents.draft_providers import _patent_from_structured

        # 复用现有 structured → PatentDraftResult 转换器，保持一致性
        return _patent_from_structured(output.model_dump())
