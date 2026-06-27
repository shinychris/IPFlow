"""商标草稿 Agent 后端（pydantic-ai + 中国商标注册技能 SKILL.md）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from ipflow.config import Settings
from ipflow.services.agent.base import BaseAgentDraftProvider


class TrademarkInfo(BaseModel):
    trademark_type: str = Field("word", description="商标类型")
    trademark_name: str = Field("", description="商标名称")
    description: str = Field("", description="商标描述")
    design_description: Optional[str] = Field(None, description="图样说明")
    color_claim: Optional[str] = Field(None, description="颜色说明")
    special_notes: Optional[str] = Field(None, description="特别声明")


class TrademarkNiceClass(BaseModel):
    class_number: int = Field(..., description="尼斯分类编号（1-45）")
    goods_services: list[str] = Field(default_factory=list, description="商品/服务项目")


class TrademarkDraftOutput(BaseModel):
    """商标草稿结构化输出（与 trademark_draft_output.schema.json 对齐）。"""

    trademark_info: TrademarkInfo
    nice_classes: list[TrademarkNiceClass]


class TrademarkAgentDraftProvider(BaseAgentDraftProvider[TrademarkDraftOutput]):
    """商标草稿 Agent 后端。"""

    output_model = TrademarkDraftOutput
    instructions_prefix = (
        "你是中国商标注册申请材料撰写助手。请根据用户提供的信息，"
        "严格按结构化输出格式生成商标「基本信息」与「尼斯分类」。"
        "严格遵循下方技能（SKILL）的规范要求。"
    )

    def get_skill_path(self) -> Path:
        cfg = self._settings
        return cfg.resolve_backend_path(cfg.CLAUDE_CODE_TRADEMARK_SKILL_PROMPT_FILE)

    def build_user_prompt(self, project: Any, inputs: dict[str, Any]) -> str:
        payload = inputs or {}
        inner = payload.get("inputs") or {}
        name = inner.get("trademark_name") or getattr(project, "name", "未命名商标")
        tm_type = inner.get("trademark_type", "word")
        brief = (inner.get("description") or inner.get("extra_brief") or "").strip()
        return (
            f"请为以下商标生成注册申请草稿材料。\n\n"
            f"商标名称：{name}\n商标类型：{tm_type}\n"
            f"简介：{brief or '（无）'}\n\n"
            f"请输出 trademark_info 与 nice_classes（至少 1 个分类，含具体商品/服务）两个字段。"
        )

    def to_draft_result(self, output: TrademarkDraftOutput, project: Any) -> Any:
        from ipflow.services.trademarks.draft_providers import (
            _trademark_from_structured,
        )

        return _trademark_from_structured(output.model_dump())
