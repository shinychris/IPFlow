"""copyright_generation schema 测试."""

from __future__ import annotations

from ipflow.schemas.generation_repo import RepoInput, parse_repo_input_from_payload


def test_repo_legacy_url_branch() -> None:
    r = RepoInput.model_validate(
        {"url": "https://github.com/o/r.git", "branch": "dev"},
    )
    assert r.effective_source_url() == "https://github.com/o/r.git"
    assert r.ref == "dev"


def test_parse_from_job_payload() -> None:
    p = parse_repo_input_from_payload(
        {
            "inputs": {
                "repo": {"source_url": "https://a.com/x.zip", "source_type": "zip"},
            },
        },
    )
    assert p is not None
    assert p.source_type == "zip"


def test_parse_empty_repo_dict() -> None:
    assert parse_repo_input_from_payload({"inputs": {"repo": {}}}) is None
