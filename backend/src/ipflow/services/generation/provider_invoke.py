"""统一：Claude Code / 模板 provider 调用与回退."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Callable

from ipflow.config import Settings


async def invoke_material_draft_provider(
    settings: Settings,
    *,
    backend_setting: str,
    fallback_setting: str,
    provider: Any,
    template_factory: Callable[[], Any],
    project: Any,
    payload: dict,
    code_root: Path | None,
) -> Any:
    """根据 *backend_setting* 决定调用方式（claude_code 线程 / agent 原生 async / 模板同步）；支持回退模板。

    - ``claude_code``：在线程中调用同步 ``generate``。
    - ``agent``（pydantic-ai）：``generate`` 为 async，直接 ``await``。
    - 其它（``template``/``llm``）：同步 ``generate``。
    """
    backend = getattr(settings, backend_setting).strip().lower()
    use_claude = backend == "claude_code"
    use_agent = backend == "agent"
    try:
        if use_claude:
            return await asyncio.to_thread(
                lambda: provider.generate(project, payload, code_root=code_root),
            )
        if use_agent:
            # pydantic-ai Agent.generate 是 async 原生
            return await provider.generate(project, payload, code_root=code_root)
        return provider.generate(project, payload, code_root=code_root)
    except Exception:
        # agent / claude_code 失败时回退到模板（若开启）
        if (use_claude or use_agent) and getattr(settings, fallback_setting):
            return template_factory().generate(project, payload, code_root=code_root)
        raise
