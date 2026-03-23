"""调用 Claude Code CLI（-p）生成结构化材料草稿（软著及通用技能入口）."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ipflow.config import Settings, get_settings
from ipflow.models import Project
from ipflow.services.copyright.draft_providers import DraftResult

logger = logging.getLogger(__name__)


class ClaudeCodeRunnerError(Exception):
    """Claude Code 执行或解析失败."""


def check_material_claude_ready(
    draft_backend: str,
    skill_path: Path,
    schema_path: Path,
    settings: Settings | None = None,
) -> str | None:
    """当 draft_backend 为 claude_code 时校验 CLI 与资源文件."""
    cfg = settings or get_settings()
    if draft_backend.strip().lower() != "claude_code":
        return None
    if not shutil.which(cfg.CLAUDE_CODE_BIN):
        return f"未找到 Claude Code CLI: {cfg.CLAUDE_CODE_BIN}"
    if not skill_path.is_file():
        return f"技能提示文件不存在: {skill_path}"
    if not schema_path.is_file():
        return f"JSON Schema 文件不存在: {schema_path}"
    return None


def check_claude_code_ready(settings: Settings | None = None) -> str | None:
    """软著：若启用 claude_code 则校验环境与资源."""
    cfg = settings or get_settings()
    return check_material_claude_ready(
        cfg.COPYRIGHT_DRAFT_BACKEND,
        cfg.resolve_backend_path(cfg.CLAUDE_CODE_SKILL_PROMPT_FILE),
        cfg.resolve_backend_path(cfg.CLAUDE_CODE_OUTPUT_SCHEMA_PATH),
        cfg,
    )


def check_patent_claude_code_ready(settings: Settings | None = None) -> str | None:
    cfg = settings or get_settings()
    return check_material_claude_ready(
        cfg.PATENT_DRAFT_BACKEND,
        cfg.resolve_backend_path(cfg.CLAUDE_CODE_PATENT_SKILL_PROMPT_FILE),
        cfg.resolve_backend_path(cfg.CLAUDE_CODE_PATENT_OUTPUT_SCHEMA_PATH),
        cfg,
    )


def check_trademark_claude_code_ready(settings: Settings | None = None) -> str | None:
    cfg = settings or get_settings()
    return check_material_claude_ready(
        cfg.TRADEMARK_DRAFT_BACKEND,
        cfg.resolve_backend_path(cfg.CLAUDE_CODE_TRADEMARK_SKILL_PROMPT_FILE),
        cfg.resolve_backend_path(cfg.CLAUDE_CODE_TRADEMARK_OUTPUT_SCHEMA_PATH),
        cfg,
    )


def _build_claude_argv(
    cfg: Settings,
    prompt: str,
    skill_path: Path,
    schema_text: str,
) -> list[str]:
    cmd: list[str] = [cfg.CLAUDE_CODE_BIN]
    if cfg.CLAUDE_CODE_BARE_MODE:
        cmd.append("--bare")
    cmd.extend(
        [
            "-p",
            prompt,
            "--output-format",
            "json",
            "--json-schema",
            schema_text,
            "--append-system-prompt-file",
            str(skill_path),
        ]
    )
    tools = cfg.claude_code_allowed_tools_list
    if tools:
        cmd.extend(["--allowedTools", ",".join(tools)])

    cmd.extend(["--max-turns", str(max(1, cfg.CLAUDE_CODE_MAX_TURNS))])

    if cfg.CLAUDE_CODE_PERMISSION_MODE and cfg.CLAUDE_CODE_PERMISSION_MODE.strip():
        cmd.extend(
            ["--permission-mode", cfg.CLAUDE_CODE_PERMISSION_MODE.strip()],
        )

    if cfg.CLAUDE_CODE_SETTINGS_FILE:
        settings_path = Path(cfg.CLAUDE_CODE_SETTINGS_FILE)
        if not settings_path.is_file():
            raise ClaudeCodeRunnerError(f"--settings 文件不存在: {settings_path}")
        cmd.extend(["--settings", str(settings_path.resolve())])
    return cmd


def structured_output_dict_from_stdout(stdout: str) -> dict[str, Any]:
    """解析 CLI JSON  stdout 中的 structured_output 对象."""
    try:
        outer = json.loads(stdout)
    except json.JSONDecodeError as e:
        tail = (stdout or "")[:2000]
        raise ClaudeCodeRunnerError(f"无法解析 CLI 输出 JSON: {e}; stdout={tail!r}") from e

    structured = outer.get("structured_output")
    if not isinstance(structured, dict):
        raise ClaudeCodeRunnerError(
            f"响应缺少 structured_output: keys={list(outer.keys())!r}",
        )
    return structured


def run_structured_claude_skill(
    project: Project,
    inputs: dict[str, Any],
    code_root: Path | None,
    *,
    skill_path: Path,
    schema_path: Path,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """执行指定 SKILL + Schema，返回 structured_output 字典."""
    cfg = settings or get_settings()
    schema_text = schema_path.read_text(encoding="utf-8")

    inner = (inputs or {}).get("inputs") or {}
    user_payload = {
        "project": {
            "id": str(project.id),
            "name": project.name,
            "version": project.version,
            "description": project.description,
            "subject_name": getattr(project, "subject_name", None),
        },
        "extra_brief": inner.get("extra_brief"),
        "policy": (inputs or {}).get("policy"),
        "code_root": str(code_root.resolve()) if code_root else None,
    }
    prompt = json.dumps(user_payload, ensure_ascii=False)
    cmd = _build_claude_argv(cfg, prompt, skill_path, schema_text)

    tmp_cwd: Path | None = None
    if code_root and code_root.is_dir():
        cwd = str(code_root.resolve())
    else:
        tmp_cwd = Path(tempfile.mkdtemp(prefix="ipflow-claude-cwd-"))
        cwd = str(tmp_cwd)

    try:
        logger.info("claude_code_invoking", extra={"cwd": cwd, "skill": str(skill_path)})
        proc = subprocess.run(  # noqa: S603
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=max(30, cfg.CLAUDE_CODE_TIMEOUT_SECONDS),
        )
    finally:
        if tmp_cwd and tmp_cwd.exists():
            shutil.rmtree(tmp_cwd, ignore_errors=True)

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "")[:4000]
        raise ClaudeCodeRunnerError(f"Claude Code 退出码 {proc.returncode}: {err}")

    return structured_output_dict_from_stdout(proc.stdout or "")


def _copyright_draft_from_structured(structured: dict[str, Any]) -> DraftResult:
    si = structured.get("software_info")
    man = structured.get("manual")
    if not isinstance(si, dict) or not isinstance(man, dict):
        raise ClaudeCodeRunnerError("structured_output 格式无效（软著）")

    si = dict(si)
    man = dict(man)
    si.setdefault("source", "ai")
    man.setdefault("source", "ai")
    if "content_json" not in man:
        man["content_json"] = None

    return DraftResult(software_info=si, manual=man)


def run_copyright_claude_draft(
    project: Project,
    inputs: dict[str, Any],
    *,
    code_root: Path | None,
    settings: Settings | None = None,
) -> DraftResult:
    cfg = settings or get_settings()
    skill_path = cfg.resolve_backend_path(cfg.CLAUDE_CODE_SKILL_PROMPT_FILE)
    schema_path = cfg.resolve_backend_path(cfg.CLAUDE_CODE_OUTPUT_SCHEMA_PATH)
    structured = run_structured_claude_skill(
        project,
        inputs,
        code_root,
        skill_path=skill_path,
        schema_path=schema_path,
        settings=cfg,
    )
    return _copyright_draft_from_structured(structured)
