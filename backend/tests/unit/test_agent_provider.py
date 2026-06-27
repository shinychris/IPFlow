"""pydantic-ai Agent 草稿后端单元测试.

使用 pydantic-ai ``TestModel`` 避免真实 API 调用，覆盖：
- ``build_agent_model`` 凭证校验与回退
- 技能（SKILL.md）加载
- 结构化输出 → DraftResult 转换（软著/专利/商标）
- Agent provider 在模型不可用时抛 AgentModelUnavailable（触发回退）
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ipflow.services.agent.models import build_agent_model, AgentModelUnavailable


# =============================================================================
# build_agent_model
# =============================================================================


def _settings(**overrides):
    """构造测试 settings（默认无凭证，含技能路径与 resolve_backend_path）。"""
    from pathlib import Path

    base = dict(
        AI_PROVIDER="ollama",
        AI_MODEL="llama3.2",
        OPENAI_API_KEY=None,
        ANTHROPIC_API_KEY=None,
        OLLAMA_BASE_URL="http://localhost:11434",
        COPYRIGHT_DRAFT_BACKEND="agent",
        PATENT_DRAFT_BACKEND="agent",
        TRADEMARK_DRAFT_BACKEND="agent",
        CLAUDE_CODE_SKILL_PROMPT_FILE="resources/skills/software-copyright-application/SKILL.md",
        CLAUDE_CODE_PATENT_SKILL_PROMPT_FILE="resources/skills/china-patent-application/SKILL.md",
        CLAUDE_CODE_TRADEMARK_SKILL_PROMPT_FILE="resources/skills/china-trademark-application/SKILL.md",
    )
    base.update(overrides)
    s = SimpleNamespace(**base)
    # resolve_backend_path：相对路径基于 backend 根目录解析
    backend_root = Path(__file__).resolve().parents[2]
    s.resolve_backend_path = lambda p: (Path(p) if Path(p).is_absolute() else backend_root / p)
    return s


class TestBuildAgentModel:
    def test_ollama_with_base_url(self) -> None:
        m = build_agent_model(_settings(AI_PROVIDER="ollama"))
        assert m == "ollama:llama3.2"

    def test_openai_with_key(self) -> None:
        m = build_agent_model(
            _settings(AI_PROVIDER="openai", AI_MODEL="gpt-4o", OPENAI_API_KEY="sk-x")
        )
        assert m == "openai:gpt-4o"

    def test_openai_without_key_raises(self) -> None:
        with pytest.raises(AgentModelUnavailable, match="OPENAI_API_KEY"):
            build_agent_model(_settings(AI_PROVIDER="openai", OPENAI_API_KEY=None))

    def test_anthropic_with_key(self) -> None:
        m = build_agent_model(
            _settings(
                AI_PROVIDER="anthropic", AI_MODEL="claude-3-5-sonnet", ANTHROPIC_API_KEY="sk-ant"
            )
        )
        assert m == "anthropic:claude-3-5-sonnet"

    def test_anthropic_without_key_raises(self) -> None:
        with pytest.raises(AgentModelUnavailable, match="ANTHROPIC_API_KEY"):
            build_agent_model(_settings(AI_PROVIDER="anthropic", ANTHROPIC_API_KEY=None))

    def test_empty_model_raises(self) -> None:
        with pytest.raises(AgentModelUnavailable, match="AI_MODEL"):
            build_agent_model(_settings(AI_MODEL=""))

    def test_unsupported_provider_raises(self) -> None:
        with pytest.raises(AgentModelUnavailable, match="不支持的 AI_PROVIDER"):
            build_agent_model(_settings(AI_PROVIDER="huggingface", AI_MODEL="x"))


# =============================================================================
# 技能加载
# =============================================================================


class TestLoadSkillInstructions:
    def test_loads_existing_skill(self, tmp_path) -> None:
        from ipflow.services.agent.base import load_skill_instructions

        skill = tmp_path / "SKILL.md"
        skill.write_text("# 技能\n## 步骤一", encoding="utf-8")
        text = load_skill_instructions(skill)
        assert "技能" in text
        assert "步骤一" in text

    def test_missing_file_returns_empty(self, tmp_path) -> None:
        from ipflow.services.agent.base import load_skill_instructions

        text = load_skill_instructions(tmp_path / "nope.md")
        assert text == ""


# =============================================================================
# 软著 Agent provider（结构化输出转换）
# =============================================================================


class TestCopyrightAgentProvider:
    def test_to_draft_result_conversion(self) -> None:
        from ipflow.services.agent.copyright_agent import (
            CopyrightAgentDraftProvider,
            CopyrightDraftOutput,
            CopyrightSoftwareInfo,
            CopyrightManual,
        )

        provider = CopyrightAgentDraftProvider(_settings())
        output = CopyrightDraftOutput(
            software_info=CopyrightSoftwareInfo(
                software_full_name="测试软件",
                software_short_name="测试",
                version_number="1.0",
                development_language="Python",
                development_environment="Linux",
                runtime_environment="Linux",
                functional_description="功能",
                technical_features="特点",
                target_domain="企业服务",
            ),
            manual=CopyrightManual(
                template_type="web", title="操作说明书", content_html="<p>x</p>"
            ),
        )
        result = provider.to_draft_result(output, SimpleNamespace(name="测试软件"))
        assert result.software_info["software_full_name"] == "测试软件"
        assert result.software_info["source"] == "ai"
        assert result.manual["title"] == "操作说明书"
        assert result.manual["source"] == "ai"

    def test_build_user_prompt_contains_project_info(self) -> None:
        from ipflow.services.agent.copyright_agent import CopyrightAgentDraftProvider

        provider = CopyrightAgentDraftProvider(_settings())
        prompt = provider.build_user_prompt(
            SimpleNamespace(name="我的软件", version="2.0"), {"inputs": {"extra_brief": "高并发"}}
        )
        assert "我的软件" in prompt
        assert "2.0" in prompt
        assert "高并发" in prompt


# =============================================================================
# 专利 Agent provider
# =============================================================================


class TestPatentAgentProvider:
    def test_to_draft_result_conversion(self) -> None:
        from ipflow.services.agent.patent_agent import (
            PatentAgentDraftProvider,
            PatentDraftOutput,
            PatentInfo,
            PatentClaim,
            PatentDescription,
            PatentInventionContent,
        )

        provider = PatentAgentDraftProvider(_settings())
        output = PatentDraftOutput(
            patent_info=PatentInfo(
                patent_type="invention",
                title="一种系统",
                technical_field="软件",
                background_art="现有不足",
                abstract="摘要",
            ),
            claims=[
                PatentClaim(
                    claim_number=1,
                    claim_type="independent",
                    parent_claim_number=None,
                    content="一种系统",
                )
            ],
            description=PatentDescription(
                technical_field="软件",
                background_art="现有不足",
                invention_content=PatentInventionContent(
                    problem_solved="问题",
                    technical_solution="方案",
                    beneficial_effects="效果",
                ),
                implementation="实施例",
            ),
        )
        result = provider.to_draft_result(output, SimpleNamespace(name="X"))
        assert result.patent_info["title"] == "一种系统"
        assert result.claims[0]["claim_number"] == 1
        assert result.description["invention_content"]["problem_solved"] == "问题"


# =============================================================================
# 商标 Agent provider
# =============================================================================


class TestTrademarkAgentProvider:
    def test_to_draft_result_conversion(self) -> None:
        from ipflow.services.agent.trademark_agent import (
            TrademarkAgentDraftProvider,
            TrademarkDraftOutput,
            TrademarkInfo,
            TrademarkNiceClass,
        )

        provider = TrademarkAgentDraftProvider(_settings())
        output = TrademarkDraftOutput(
            trademark_info=TrademarkInfo(
                trademark_type="word", trademark_name="IPFlow", description="测试"
            ),
            nice_classes=[
                TrademarkNiceClass(class_number=9, goods_services=["软件"])
            ],
        )
        result = provider.to_draft_result(output, SimpleNamespace(name="X"))
        assert result.trademark_info["trademark_name"] == "IPFlow"
        assert result.nice_classes[0]["class_number"] == 9
        assert result.nice_classes[0]["goods_services"] == ["软件"]


# =============================================================================
# Agent 运行（TestModel，零真实 API 调用）
# =============================================================================


class TestAgentRunWithTestModel:
    """用 TestModel 注入 Agent，验证 generate 端到端（无真实 LLM）。"""

    def test_copyright_generate_with_testmodel(self) -> None:
        from pydantic_ai.models.test import TestModel
        from ipflow.services.agent.copyright_agent import (
            CopyrightAgentDraftProvider,
            CopyrightDraftOutput,
            CopyrightSoftwareInfo,
            CopyrightManual,
        )

        provider = CopyrightAgentDraftProvider(_settings())
        # 指定 TestModel 自定义输出（结构化 pydantic 对象）
        test_model = TestModel()
        test_model.custom_output_args = CopyrightDraftOutput(
            software_info=CopyrightSoftwareInfo(
                software_full_name="TestSoftware"
            ),
            manual=CopyrightManual(title="手册", content_html="<p>x</p>"),
        )

        with patch("ipflow.services.agent.base.build_agent_model", return_value=test_model):
            result = asyncio.run(
                provider.generate(
                    SimpleNamespace(name="TestSoftware", version="1.0"), {"inputs": {}}
                )
            )
        assert result.software_info["software_full_name"] == "TestSoftware"
        assert result.manual["title"] == "手册"

    def test_generate_raises_when_model_unavailable(self) -> None:
        """凭证缺失时 _build_agent 抛 AgentModelUnavailable（触发 provider_invoke 回退）。"""
        from ipflow.services.agent.copyright_agent import CopyrightAgentDraftProvider

        provider = CopyrightAgentDraftProvider(
            _settings(AI_PROVIDER="openai", OPENAI_API_KEY=None)
        )
        with pytest.raises(AgentModelUnavailable):
            asyncio.run(
                provider.generate(
                    SimpleNamespace(name="X", version="1"), {"inputs": {}}
                )
            )


# =============================================================================
# 工厂集成（agent 后端被选中）
# =============================================================================


class TestFactoryIntegration:
    def test_copyright_factory_returns_agent_provider(self) -> None:
        from ipflow.services.copyright.draft_providers import (
            get_copyright_draft_provider,
        )
        from ipflow.services.agent.copyright_agent import CopyrightAgentDraftProvider

        provider = get_copyright_draft_provider(
            _settings(COPYRIGHT_DRAFT_BACKEND="agent")
        )
        assert isinstance(provider, CopyrightAgentDraftProvider)

    def test_patent_factory_returns_agent_provider(self) -> None:
        from ipflow.services.patents.draft_providers import get_patent_draft_provider
        from ipflow.services.agent.patent_agent import PatentAgentDraftProvider

        provider = get_patent_draft_provider(_settings(PATENT_DRAFT_BACKEND="agent"))
        assert isinstance(provider, PatentAgentDraftProvider)

    def test_trademark_factory_returns_agent_provider(self) -> None:
        from ipflow.services.trademarks.draft_providers import (
            get_trademark_draft_provider,
        )
        from ipflow.services.agent.trademark_agent import TrademarkAgentDraftProvider

        provider = get_trademark_draft_provider(
            _settings(TRADEMARK_DRAFT_BACKEND="agent")
        )
        assert isinstance(provider, TrademarkAgentDraftProvider)
