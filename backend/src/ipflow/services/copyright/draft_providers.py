"""软著草稿生成：模板实现与 Claude Code CLI 实现."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from ipflow.config import Settings, get_settings
from ipflow.models import Project

logger = logging.getLogger(__name__)


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


class LLMCopyrightDraftProvider:
    """通过通用 LLM 服务（Ollama/OpenAI/Anthropic）生成草稿.

    将此前孤立的 ``llm_service`` 接入草稿生成主流程：构造提示词调用配置的
    LLM 提供商，解析返回的 JSON 作为草稿内容。LLM 不可用时回退到模板。
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._fallback = TemplateCopyrightDraftProvider()

    def _build_prompt(self, project: Project, inputs: dict[str, Any]) -> list[dict[str, str]]:
        """构造生成草稿的提示词."""
        payload = inputs or {}
        inner = payload.get("inputs") or {}
        extra_brief = (inner.get("extra_brief") or "").strip()
        software_name = project.name
        version = project.version or "1.0"

        system = (
            "你是软件著作权申报材料撰写助手。请根据用户提供的软件信息，"
            "生成中国软件著作权登记所需的「软件基本信息」与「操作说明书」草稿。"
            "严格按 JSON 输出，不要任何额外文字。"
        )
        schema_hint = {
            "software_info": {
                "software_full_name": "软件全称",
                "software_short_name": "简称（≤20字）",
                "version_number": "版本号",
                "development_language": "开发语言",
                "development_environment": "开发环境",
                "runtime_environment": "运行环境",
                "functional_description": "功能描述（100-300字）",
                "technical_features": "技术特点（100-200字）",
                "target_domain": "应用领域",
            },
            "manual": {
                "title": "操作说明书标题",
                "content_html": "HTML 正文，含产品概述、功能模块、操作流程等章节",
            },
        }
        user = (
            f"软件名称：{software_name}\n版本：{version}\n"
            f"补充说明：{extra_brief or '（无）'}\n\n"
            f"请按如下 JSON 结构输出（不要包含 Markdown 代码块标记）：\n"
            f"{json.dumps(schema_hint, ensure_ascii=False, indent=2)}"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def _parse_llm_json(self, content: str, project: Project) -> DraftResult:
        """解析 LLM 返回的 JSON；失败则回退模板."""
        text = content.strip()
        # 去除可能的 Markdown 代码块标记（兼容单行 ```json{...}``` 与多行围栏）
        text = re.sub(r"^\s*```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
        text = text.strip()
        try:
            data = json.loads(text)
            software_info = data.get("software_info", {})
            manual_data = data.get("manual", {})
            software_info.setdefault("source", "ai")
            manual = {
                "template_type": "web",
                "title": manual_data.get("title", f"{project.name} 操作说明书"),
                "content_html": manual_data.get("content_html", ""),
                "content_json": None,
                "source": "ai",
            }
            return DraftResult(software_info=software_info, manual=manual)
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning("LLM 草稿 JSON 解析失败，回退模板：%s", e)
            return self._fallback.generate(project, {})

    def generate(
        self,
        project: Project,
        inputs: dict[str, Any],
        *,
        code_root: Any | None = None,
    ) -> DraftResult:
        from ipflow.services.llm_service import LLMMessage, get_llm_service

        messages = self._build_prompt(project, inputs)
        try:
            service = get_llm_service()
            # provider.chat 是协程，在同步 generate 中通过事件循环执行
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():  # 已在异步上下文（不应发生在后台线程）
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        response = pool.submit(
                            lambda: asyncio.run(service.chat(
                                [LLMMessage(role=m["role"], content=m["content"]) for m in messages]
                            ))
                        ).result()
                else:
                    response = loop.run_until_complete(
                        service.chat(
                            [LLMMessage(role=m["role"], content=m["content"]) for m in messages]
                        )
                    )
            except RuntimeError:
                response = asyncio.run(
                    service.chat(
                        [LLMMessage(role=m["role"], content=m["content"]) for m in messages]
                    )
                )
            return self._parse_llm_json(response.content, project)
        except Exception as e:  # noqa: BLE001
            logger.warning("LLM 草稿生成失败，回退模板：%s", e)
            return self._fallback.generate(project, inputs)


def get_copyright_draft_provider(
    settings: Settings | None = None,
) -> (
    TemplateCopyrightDraftProvider
    | ClaudeCodeCopyrightDraftProvider
    | LLMCopyrightDraftProvider
    | "CopyrightAgentDraftProvider"
):
    cfg = settings or get_settings()
    backend = cfg.COPYRIGHT_DRAFT_BACKEND.strip().lower()
    if backend == "claude_code":
        return ClaudeCodeCopyrightDraftProvider(cfg)
    if backend == "llm":
        return LLMCopyrightDraftProvider(cfg)
    if backend == "agent":
        # 惰性导入 pydantic-ai 依赖，避免无该后端时引入硬依赖
        from ipflow.services.agent.copyright_agent import CopyrightAgentDraftProvider

        return CopyrightAgentDraftProvider(cfg)
    return TemplateCopyrightDraftProvider()
