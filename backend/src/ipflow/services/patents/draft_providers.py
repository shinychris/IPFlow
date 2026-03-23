"""专利草稿：模板与 Claude Code."""

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
class PatentDraftResult:
    patent_info: dict[str, Any]
    claims: list[dict[str, Any]]
    description: dict[str, Any]


class TemplatePatentDraftProvider:
    def generate(
        self,
        project: Project,
        inputs: dict[str, Any],
        *,
        code_root: Any | None = None,
    ) -> PatentDraftResult:
        payload = inputs or {}
        extra_brief = (payload.get("inputs", {}) or {}).get("extra_brief", "")
        title = project.name

        patent_info = {
            "patent_type": "invention",
            "title": title,
            "technical_field": "本发明涉及软件系统与流程自动化技术领域。",
            "background_art": extra_brief or "现有方案在资料生成效率与一致性方面存在不足。",
            "abstract": f"本发明公开了一种用于{title}的自动化处理方法与系统。",
            "abstract_figure_number": None,
        }

        claims = [
            {
                "claim_number": 1,
                "claim_type": "independent",
                "parent_claim_number": None,
                "content": "一种自动化资料生成系统，其特征在于包括任务编排模块、数据处理模块与导出模块。",
            },
            {
                "claim_number": 2,
                "claim_type": "dependent",
                "parent_claim_number": 1,
                "content": "根据权利要求1所述系统，其特征在于所述任务编排模块支持生成状态追踪与失败重试。",
            },
        ]

        description = {
            "technical_field": patent_info["technical_field"],
            "background_art": patent_info["background_art"],
            "invention_content": {
                "problem_solved": "解决人工整理材料耗时且易遗漏的问题。",
                "technical_solution": "通过任务化生成与结构化编辑实现自动草稿产出。",
                "beneficial_effects": "提升专利文档准备效率并减少一致性错误。",
            },
            "implementation": "系统接收项目输入后生成草稿，用户在工作台编辑确认后导出。",
        }

        return PatentDraftResult(patent_info=patent_info, claims=claims, description=description)


def _patent_from_structured(structured: dict[str, Any]) -> PatentDraftResult:
    pi = structured.get("patent_info")
    claims_raw = structured.get("claims")
    desc = structured.get("description")
    if not isinstance(pi, dict) or not isinstance(claims_raw, list) or not isinstance(desc, dict):
        raise ClaudeCodeRunnerError("专利 structured_output 顶层格式无效")
    ic = desc.get("invention_content")
    if not isinstance(ic, dict):
        raise ClaudeCodeRunnerError("专利 description.invention_content 无效")
    norm_claims: list[dict[str, Any]] = []
    for c in claims_raw:
        if not isinstance(c, dict):
            raise ClaudeCodeRunnerError("专利 claims 项格式无效")
        norm_claims.append(
            {
                "claim_number": int(c["claim_number"]),
                "claim_type": str(c["claim_type"]),
                "parent_claim_number": c.get("parent_claim_number"),
                "content": str(c["content"]),
            },
        )
    return PatentDraftResult(patent_info=dict(pi), claims=norm_claims, description=dict(desc))


class ClaudePatentDraftProvider:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def generate(
        self,
        project: Project,
        inputs: dict[str, Any],
        *,
        code_root: Any | None = None,
    ) -> PatentDraftResult:
        cfg = self._settings
        sp = cfg.resolve_backend_path(cfg.CLAUDE_CODE_PATENT_SKILL_PROMPT_FILE)
        sch = cfg.resolve_backend_path(cfg.CLAUDE_CODE_PATENT_OUTPUT_SCHEMA_PATH)
        root = code_root if code_root is not None else None
        structured = run_structured_claude_skill(
            project,
            inputs,
            root,
            skill_path=sp,
            schema_path=sch,
            settings=cfg,
        )
        return _patent_from_structured(structured)


def get_patent_draft_provider(settings: Settings | None = None) -> TemplatePatentDraftProvider | ClaudePatentDraftProvider:
    cfg = settings or get_settings()
    if cfg.PATENT_DRAFT_BACKEND.strip().lower() == "claude_code":
        return ClaudePatentDraftProvider(cfg)
    return TemplatePatentDraftProvider()
