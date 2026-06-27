"""pydantic-ai 模型构建.

按 ``AI_PROVIDER``（``openai`` / ``anthropic`` / ``ollama``）与 ``AI_MODEL``
构建 pydantic-ai 模型。缺失 API Key / 服务地址时抛出 ``AgentModelUnavailable``，
由上层捕获后回退到 template 后端（保证无凭证环境不崩）。

优先采用 pydantic-ai 内置的「提供商前缀模型名」（如 ``openai:gpt-4o``），
让框架自动从环境变量读取凭证，避免与各 SDK 客户端构造细节耦合，是最稳定的 API。
"""

from __future__ import annotations

from typing import Any, Optional

from ipflow.config import Settings, get_settings


class AgentModelUnavailable(RuntimeError):
    """Agent 模型不可用（缺少 API Key / 服务未配置）。

    捕获后应由调用方回退到 template 后端。
    """


def _normalize(provider: str) -> str:
    return (provider or "").strip().lower()


def build_agent_model(settings: Optional[Settings] = None) -> str:
    """根据配置返回 pydantic-ai 的「提供商前缀模型名」字符串。

    pydantic-ai ``Agent`` 接受 ``model: Model | KnownModelName | str``；
    返回形如 ``"openai:gpt-4o"`` 的字符串，框架内部会按前缀实例化对应
    ``OpenAIChatModel`` / ``AnthropicModel`` / ``OllamaModel`` 并读取环境凭证。

    Args:
        settings: 配置（默认读取全局 settings）

    Returns:
        形如 ``"<provider>:<model>"`` 的模型名字符串

    Raises:
        AgentModelUnavailable: 提供商不支持、模型名为空、或缺少必需凭证
    """
    cfg = settings or get_settings()
    provider = _normalize(cfg.AI_PROVIDER)
    model = (cfg.AI_MODEL or "").strip()

    if not model:
        raise AgentModelUnavailable("AI_MODEL 未配置，无法构建 Agent 模型")

    if provider == "openai":
        if not (cfg.OPENAI_API_KEY or "").strip():
            raise AgentModelUnavailable("OPENAI_API_KEY 未配置，无法使用 OpenAI Agent")
        return f"openai:{model}"

    if provider == "anthropic":
        if not (cfg.ANTHROPIC_API_KEY or "").strip():
            raise AgentModelUnavailable("ANTHROPIC_API_KEY 未配置，无法使用 Anthropic Agent")
        return f"anthropic:{model}"

    if provider == "ollama":
        if not (cfg.OLLAMA_BASE_URL or "").strip():
            raise AgentModelUnavailable("OLLAMA_BASE_URL 未配置，无法使用 Ollama Agent")
        return f"ollama:{model}"

    raise AgentModelUnavailable(
        f"不支持的 AI_PROVIDER: {provider!r}（支持 openai / anthropic / ollama）"
    )
