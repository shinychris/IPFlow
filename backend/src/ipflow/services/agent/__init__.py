"""pydantic-ai Agent 后端：基于「skill」生成知识产权草稿材料.

该后端以仓库内版本化的 SKILL.md 作为 Agent 系统提示词（与 Claude Code CLI
后端共用同一份技能资源），通过 pydantic-ai 的结构化输出（``output_type``）
约束返回 JSON，无需调用外部 ``claude`` 进程。

启用方式：将 ``COPYRIGHT_DRAFT_BACKEND`` / ``PATENT_DRAFT_BACKEND`` /
``TRADEMARK_DRAFT_BACKEND`` 设为 ``agent``，并配置 ``AI_PROVIDER`` /
``AI_MODEL`` 及对应的 API Key（``OPENAI_API_KEY`` / ``ANTHROPIC_API_KEY`` /
``OLLAMA_BASE_URL``）。
"""

from ipflow.services.agent.models import build_agent_model, AgentModelUnavailable

__all__ = ["build_agent_model", "AgentModelUnavailable"]
