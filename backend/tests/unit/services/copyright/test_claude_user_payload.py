"""确认生成任务 input_payload → Claude 用户 JSON 的字段传递."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

from ipflow.api.v1.copyright.generation_jobs import (
    GenerationInputs,
    GenerationPolicy,
    StartGenerationRequest,
)
from ipflow.models.enums import SubjectType
from ipflow.schemas.generation_repo import RepoInput
from ipflow.services.copyright.claude_code_runner import (
    _repo_for_prompt,
    build_claude_user_json_payload,
)


def test_start_request_model_dump_feeds_build_payload(tmp_path) -> None:
    """与 POST generation-jobs 落库的 payload 结构一致."""
    req = StartGenerationRequest(
        generation_mode="guided_confirm",
        inputs=GenerationInputs(
            extra_brief="用户补充说明",
            repo=RepoInput(
                source_type="git",
                source_url="https://github.com/org/repo",
                ref="main",
            ),
            history_reuse={"enabled": True, "source_project_ids": []},
            org_knowledge={"enabled": False, "dataset_ids": []},
        ),
        policy=GenerationPolicy(overwrite_strategy="fill_blank_only"),
    )
    stored = req.model_dump(mode="json")

    project = MagicMock()
    project.id = uuid4()
    project.name = "测试软著"
    project.version = "V1.0"
    project.description = "项目描述"
    project.subject_type = SubjectType.ENTERPRISE
    project.subject_name = "某某公司"
    project.development_method = "independent"
    project.publication_status = "unpublished"
    project.completion_date = date(2025, 1, 15)
    project.first_publication_date = None
    project.meta_info = {"foo": "bar"}

    skill_root = tmp_path / "skill"
    skill_root.mkdir()
    code_root = tmp_path / "code"
    code_root.mkdir()

    out = build_claude_user_json_payload(project, stored, code_root, skill_root)

    assert out["generation_mode"] == "guided_confirm"
    assert out["policy"] == {"overwrite_strategy": "fill_blank_only"}
    assert out["inputs"]["extra_brief"] == "用户补充说明"
    assert out["inputs"]["repo"] == {
        "source_type": "git",
        "source_url": "https://github.com/org/repo",
        "ref": "main",
    }
    assert out["inputs"]["history_reuse"]["enabled"] is True
    assert out["inputs"]["org_knowledge"]["enabled"] is False
    assert out["project"]["name"] == "测试软著"
    assert out["project"]["subject_type"] == SubjectType.ENTERPRISE.value
    assert out["project"]["subject_name"] == "某某公司"
    assert out["project"]["completion_date"] == "2025-01-15"
    assert out["project"]["first_publication_date"] is None
    assert out["project"]["meta_info"] == {"foo": "bar"}
    assert out["paths"]["code_root"] == str(code_root.resolve())
    assert out["paths"]["skill_root"] == str(skill_root.resolve())
    assert "ipflow_structured_material_draft" in out["task"]


def test_repo_legacy_url_branch_dict() -> None:
    """兼容仅含 url/branch 的字典（旧客户端或 JSON 回读）."""
    assert _repo_for_prompt(
        {"url": "https://example.com/a.git", "branch": "dev", "source_type": "auto"},
    ) == {
        "source_type": "auto",
        "source_url": "https://example.com/a.git",
        "ref": "dev",
    }


def test_empty_repo_omitted() -> None:
    assert _repo_for_prompt({}) is None
    assert _repo_for_prompt(None) is None
