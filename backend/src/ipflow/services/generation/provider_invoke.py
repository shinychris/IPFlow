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
    """根据 *backend_setting* 决定是否在线程中调用 Claude provider；支持回退模板。"""
    backend = getattr(settings, backend_setting).strip().lower()
    use_claude = backend == "claude_code"
    try:
        if use_claude:
            return await asyncio.to_thread(
                lambda: provider.generate(project, payload, code_root=code_root),
            )
        return provider.generate(project, payload, code_root=code_root)
    except Exception:
        if use_claude and getattr(settings, fallback_setting):
            return template_factory().generate(project, payload, code_root=code_root)
        raise
