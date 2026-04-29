"""claude_code_runner 单元测试."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from ipflow.services.copyright.claude_code_runner import (
    ClaudeCodeRunnerError,
    run_copyright_claude_draft,
)
from ipflow.services.copyright.draft_providers import DraftResult


@pytest.fixture
def minimal_project() -> MagicMock:
    p = MagicMock()
    p.id = uuid4()
    p.name = "测试项目"
    p.version = "1.0"
    p.description = "desc"
    p.subject_name = "申请人"
    return p


def test_run_copyright_claude_draft_parses_structured_output(
    minimal_project: MagicMock,
    tmp_path: Path,
) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("# skill", encoding="utf-8")
    schema = tmp_path / "schema.json"
    schema.write_text('{"type":"object"}', encoding="utf-8")

    class _Cfg:
        CLAUDE_CODE_BIN = "claude"
        CLAUDE_CODE_SKILL_PROMPT_FILE = str(skill)
        CLAUDE_CODE_OUTPUT_SCHEMA_PATH = str(schema)
        CLAUDE_CODE_BARE_MODE = True
        CLAUDE_CODE_ALLOWED_TOOLS = "Read"
        CLAUDE_CODE_MAX_TURNS = 8
        CLAUDE_CODE_TIMEOUT_SECONDS = 30
        CLAUDE_CODE_PERMISSION_MODE = None
        CLAUDE_CODE_SETTINGS_FILE = None

        @property
        def claude_code_allowed_tools_list(self) -> list[str]:
            return [t.strip() for t in self.CLAUDE_CODE_ALLOWED_TOOLS.split(",") if t.strip()]

        def resolve_backend_path(self, p: str) -> Path:
            x = Path(p)
            return x if x.is_absolute() else tmp_path / x

    out = {
        "structured_output": {
            "software_info": {
                "software_full_name": "测试项目",
                "software_short_name": "测试",
                "version_number": "1.0",
                "development_language": "Python",
                "development_environment": "Linux",
                "runtime_environment": "Server",
                "code_line_count": None,
                "functional_description": "功能",
                "technical_features": "特点",
                "target_domain": "通用",
            },
            "manual": {
                "template_type": "web",
                "title": "说明书",
                "content_html": "<p>hi</p>",
                "content_json": None,
            },
        }
    }

    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = json.dumps(out)
    proc.stderr = ""

    cfg = _Cfg()
    with patch(
        "ipflow.services.copyright.claude_code_runner.subprocess.run",
        return_value=proc,
    ) as run_mock:
        dr = run_copyright_claude_draft(
            minimal_project,
            {"inputs": {"extra_brief": "brief"}},
            code_root=None,
            settings=cfg,  # type: ignore[arg-type]
        )
        assert isinstance(dr, DraftResult)
        assert dr.software_info["software_full_name"] == "测试项目"
        assert "<p>hi</p>" in dr.manual["content_html"]
        run_mock.assert_called_once()
        call_kw = run_mock.call_args.kwargs
        assert call_kw["cwd"] == str(skill.parent.resolve())
        assert call_kw.get("env", {}).get("PYTHONIOENCODING") == "utf-8"
        argv = run_mock.call_args.args[0]
        p_idx = list(argv).index("-p")
        prompt = argv[p_idx + 1]
        assert '"task": "ipflow_structured_material_draft"' in prompt
        assert '"extra_brief": "brief"' in prompt


def test_run_copyright_claude_draft_nonzero_exit(
    minimal_project: MagicMock,
    tmp_path: Path,
) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("# skill", encoding="utf-8")
    schema = tmp_path / "schema.json"
    schema.write_text("{}", encoding="utf-8")

    class _Cfg:
        CLAUDE_CODE_BIN = "claude"
        CLAUDE_CODE_SKILL_PROMPT_FILE = str(skill)
        CLAUDE_CODE_OUTPUT_SCHEMA_PATH = str(schema)
        CLAUDE_CODE_BARE_MODE = False
        CLAUDE_CODE_ALLOWED_TOOLS = ""
        CLAUDE_CODE_MAX_TURNS = 1
        CLAUDE_CODE_TIMEOUT_SECONDS = 5
        CLAUDE_CODE_PERMISSION_MODE = None
        CLAUDE_CODE_SETTINGS_FILE = None

        @property
        def claude_code_allowed_tools_list(self) -> list[str]:
            return [t.strip() for t in self.CLAUDE_CODE_ALLOWED_TOOLS.split(",") if t.strip()]

        def resolve_backend_path(self, p: str) -> Path:
            x = Path(p)
            return x if x.is_absolute() else tmp_path / x

    proc = MagicMock()
    proc.returncode = 1
    proc.stdout = ""
    proc.stderr = "boom"

    cfg = _Cfg()
    with patch(
        "ipflow.services.copyright.claude_code_runner.subprocess.run",
        return_value=proc,
    ):
        with pytest.raises(ClaudeCodeRunnerError, match="退出码"):
            run_copyright_claude_draft(
                minimal_project,
                {},
                code_root=None,
                settings=cfg,  # type: ignore[arg-type]
            )
