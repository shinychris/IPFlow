"""source_fetcher 单元测试."""

from __future__ import annotations

import pytest

from ipflow.config import Settings
from ipflow.schemas.generation_repo import RepoInput
from ipflow.services.copyright.source_fetcher import (
    SourceFetchError,
    assert_host_allowed,
    classify_source_kind,
)


def _settings(hosts: str) -> Settings:
    return Settings(
        SECRET_KEY="x",
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
        REDIS_URL="redis://localhost:6379/0",
        SOURCE_FETCH_ALLOWED_HOSTS=hosts,
    )


def test_classify_zip_by_extension() -> None:
    r = RepoInput(
        source_type="auto",
        source_url="https://example.com/a/b.zip",
    )
    assert classify_source_kind(r) == "zip"


def test_classify_git_ssh() -> None:
    r = RepoInput(source_type="auto", source_url="git@github.com:org/repo.git")
    assert classify_source_kind(r) == "git"


def test_classify_explicit_zip() -> None:
    r = RepoInput(source_type="zip", source_url="https://example.com/file")
    assert classify_source_kind(r) == "zip"


def test_host_allowed_https() -> None:
    s = _settings("github.com,example.org")
    assert_host_allowed("https://github.com/org/repo.git", "git", s)


def test_host_not_allowed() -> None:
    s = _settings("github.com")
    with pytest.raises(SourceFetchError, match="不在允许列表"):
        assert_host_allowed("https://evil.com/x.git", "git", s)


def test_empty_allowlist_denies() -> None:
    s = _settings("")
    with pytest.raises(SourceFetchError, match="未配置"):
        assert_host_allowed("https://github.com/x", "git", s)
