"""根据任务 payload 解析并拉取可选源码目录."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from ipflow.config import Settings, get_settings
from ipflow.schemas.generation_repo import parse_repo_input_from_payload
from ipflow.services.copyright.source_fetcher import fetch_source_to_directory


async def fetch_code_root_for_job(
    job_id: UUID,
    input_payload: dict | None,
    *,
    settings: Settings | None = None,
) -> tuple[Path | None, bool]:
    """返回 (code_root, should_cleanup)。无 repo URL 时 (None, False)。"""
    cfg = settings or get_settings()
    repo = parse_repo_input_from_payload(input_payload)
    active = repo if repo and repo.effective_source_url() else None
    if active is None:
        return None, False
    path = await fetch_source_to_directory(active, job_id, settings=cfg)
    return path, True
