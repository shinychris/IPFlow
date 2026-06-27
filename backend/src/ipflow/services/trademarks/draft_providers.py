"""商标草稿：模板与 Claude Code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ipflow.config import Settings, get_settings
from ipflow.models import Project
from ipflow.services.copyright.claude_code_runner import (
    ClaudeCodeRunnerError,
    run_structured_claude_skill,
)


@dataclass
class TrademarkDraftResult:
    trademark_info: dict[str, Any]
    nice_classes: list[dict[str, Any]]


class TemplateTrademarkDraftProvider:
    def generate(
        self,
        project: Project,
        inputs: dict[str, Any],
        *,
        code_root: Any | None = None,
    ) -> TrademarkDraftResult:
        payload = inputs or {}
        extra_brief = (payload.get("inputs", {}) or {}).get("extra_brief", "")
        trademark_name = project.name[:20]

        info = {
            "trademark_type": "word",
            "trademark_name": trademark_name,
            "description": extra_brief or f"{trademark_name} 作为品牌标识用于相关服务。",
            "design_description": None,
            "color_claim": None,
            "special_notes": "AI 草稿，可在详情页自由编辑。",
        }
        nice_classes = [
            {"class_number": 35, "goods_services": ["广告宣传", "商业管理辅助"]},
            {"class_number": 42, "goods_services": ["软件设计与开发", "技术咨询服务"]},
        ]
        return TrademarkDraftResult(trademark_info=info, nice_classes=nice_classes)


def _trademark_from_structured(structured: dict[str, Any]) -> TrademarkDraftResult:
    info = structured.get("trademark_info")
    nraw = structured.get("nice_classes")
    if not isinstance(info, dict) or not isinstance(nraw, list):
        raise ClaudeCodeRunnerError("商标 structured_output 顶层格式无效")
    nice: list[dict[str, Any]] = []
    for row in nraw:
        if not isinstance(row, dict):
            raise ClaudeCodeRunnerError("商标 nice_classes 项无效")
        gs = row.get("goods_services")
        if not isinstance(gs, list):
            raise ClaudeCodeRunnerError("goods_services 须为数组")
        nice.append(
            {
                "class_number": int(row["class_number"]),
                "goods_services": [str(x) for x in gs],
            },
        )
    return TrademarkDraftResult(trademark_info=dict(info), nice_classes=nice)


class ClaudeTrademarkDraftProvider:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def generate(
        self,
        project: Project,
        inputs: dict[str, Any],
        *,
        code_root: Any | None = None,
    ) -> TrademarkDraftResult:
        cfg = self._settings
        sp = cfg.resolve_backend_path(cfg.CLAUDE_CODE_TRADEMARK_SKILL_PROMPT_FILE)
        sch = cfg.resolve_backend_path(cfg.CLAUDE_CODE_TRADEMARK_OUTPUT_SCHEMA_PATH)
        root = code_root if code_root is not None else None
        structured = run_structured_claude_skill(
            project,
            inputs,
            root,
            skill_path=sp,
            schema_path=sch,
            settings=cfg,
        )
        return _trademark_from_structured(structured)


def get_trademark_draft_provider(
    settings: Settings | None = None,
) -> (
    TemplateTrademarkDraftProvider
    | ClaudeTrademarkDraftProvider
    | "TrademarkAgentDraftProvider"
):
    cfg = settings or get_settings()
    backend = cfg.TRADEMARK_DRAFT_BACKEND.strip().lower()
    if backend == "claude_code":
        return ClaudeTrademarkDraftProvider(cfg)
    if backend == "agent":
        from ipflow.services.agent.trademark_agent import (
            TrademarkAgentDraftProvider,
        )

        return TrademarkAgentDraftProvider(cfg)
    return TemplateTrademarkDraftProvider()
