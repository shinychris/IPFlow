"""材料生成任务中的远程源码字段（软著/专利/商标共用）."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, model_validator


class RepoInput(BaseModel):
    """远程源码说明：Git（HTTPS/SSH）或直链 zip。"""

    source_type: Literal["auto", "git", "zip"] = "auto"
    source_url: str | None = None
    ref: str | None = None
    # 兼容旧前端：url / branch / provider
    url: str | None = None
    branch: str | None = None
    provider: str | None = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def merge_legacy_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if not (out.get("source_url") or "").strip() and (out.get("url") or "").strip():
            out["source_url"] = out["url"]
        if out.get("ref") is None and (out.get("branch") or "").strip():
            out["ref"] = out["branch"]
        return out

    def effective_source_url(self) -> str | None:
        u = (self.source_url or "").strip()
        return u or None


def parse_repo_input_from_payload(payload: dict[str, Any] | None) -> RepoInput | None:
    """从 job.input_payload['inputs']['repo'] 解析."""
    if not payload:
        return None
    inputs = payload.get("inputs") or {}
    raw = inputs.get("repo")
    if raw is None:
        return None
    if isinstance(raw, RepoInput):
        return raw
    if isinstance(raw, dict) and not any(
        (raw.get("source_url") or raw.get("url") or "").strip(),
    ):
        return None
    return RepoInput.model_validate(raw)
