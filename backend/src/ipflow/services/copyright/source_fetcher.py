"""从用户提供的 URL 拉取 Git 仓库或 zip 源码（受 host 白名单约束）."""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import httpx

from ipflow.config import Settings, get_settings
from ipflow.schemas.generation_repo import RepoInput

logger = logging.getLogger(__name__)


class SourceFetchError(Exception):
    """拉取或解压源码失败."""


def classify_source_kind(repo: RepoInput) -> str:
    """返回 git 或 zip."""
    url = (repo.effective_source_url() or "").strip()
    st = repo.source_type
    if st == "zip":
        return "zip"
    if st == "git":
        return "git"
    if url.lower().startswith("git@") or url.lower().startswith("ssh://"):
        return "git"
    if url.lower().rstrip("/").endswith(".zip"):
        return "zip"
    return "git"


def _host_from_git_ssh(url: str) -> str:
    u = url.strip()
    if u.startswith("git@"):
        before_colon = u.split(":", 1)[0]
        return before_colon.removeprefix("git@").lower()
    if u.startswith("ssh://"):
        parsed = urlparse(u)
        return (parsed.hostname or "").lower()
    return ""


def _host_from_https(url: str) -> str:
    parsed = urlparse(url.strip())
    return (parsed.hostname or "").lower()


def _redact_url_for_log(url: str) -> str:
    try:
        p = urlparse(url.strip())
        if p.username or p.password:
            netloc = p.hostname or ""
            if p.port:
                netloc = f"{netloc}:{p.port}"
            return p._replace(netloc=netloc, username=None, password=None).geturl()
    except Exception:
        pass
    return url


def assert_host_allowed(url: str, kind: str, settings: Settings) -> None:
    allowed = settings.source_fetch_allowed_hosts_list
    if not allowed:
        raise SourceFetchError("未配置允许的源码主机（SOURCE_FETCH_ALLOWED_HOSTS），已禁止远程拉取")

    if kind == "git" and (
        url.strip().lower().startswith("git@") or url.strip().lower().startswith("ssh://")
    ):
        host = _host_from_git_ssh(url)
    else:
        if not url.strip().lower().startswith(("http://", "https://")):
            raise SourceFetchError("zip 或 Git HTTPS 仅支持 http(s) 链接")
        host = _host_from_https(url)

    if not host:
        raise SourceFetchError("无法解析 URL 主机名")

    if host not in allowed:
        raise SourceFetchError(f"主机不在允许列表中: {host}")


def _git_clone(url: str, ref: str | None, repo_dir: Path, cfg: Settings) -> None:
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    depth = max(1, cfg.GIT_CLONE_DEPTH)
    cmd = [
        "git",
        "clone",
        "--depth",
        str(depth),
        url,
        str(repo_dir),
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "")[:2000]
        raise SourceFetchError(f"git clone 失败: {err}") from e
    except subprocess.TimeoutExpired as e:
        raise SourceFetchError("git clone 超时") from e

    if ref and ref.strip():
        try:
            subprocess.run(
                ["git", "-C", str(repo_dir), "fetch", "--depth", str(depth), "origin", ref],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            subprocess.run(
                ["git", "-C", str(repo_dir), "checkout", ref],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout or "")[:2000]
            raise SourceFetchError(f"git checkout 失败: {err}") from e


def _download_and_unzip(url: str, work_dir: Path, extract_root: Path, cfg: Settings) -> None:
    max_bytes = cfg.SOURCE_FETCH_MAX_ZIP_BYTES
    zip_path = work_dir / "_download.zip"
    extract_root.mkdir(parents=True, exist_ok=True)

    with httpx.Client(follow_redirects=True, timeout=600.0) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            total = 0
            with open(zip_path, "wb") as f:
                for chunk in resp.iter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        raise SourceFetchError("zip 下载超过大小上限")
                    f.write(chunk)

    extracted = 0
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                name = member.filename
                if not name or name.startswith("/"):
                    raise SourceFetchError(f"非法 zip 路径: {name!r}")
                parts = Path(name).parts
                if ".." in parts:
                    raise SourceFetchError(f"非法 zip 路径: {name!r}")
                dest_path = (extract_root / name).resolve()
                extract_resolved = extract_root.resolve()
                try:
                    dest_path.relative_to(extract_resolved)
                except ValueError as e:
                    raise SourceFetchError("zip 路径穿越被拒绝") from e
                estimated = extracted + member.file_size
                if estimated > cfg.SOURCE_FETCH_MAX_EXTRACTED_BYTES:
                    raise SourceFetchError("解压后总大小超过上限")
                zf.extract(member, extract_root)
                extracted += member.file_size
    except zipfile.BadZipFile as e:
        raise SourceFetchError("不是有效的 zip 文件") from e
    finally:
        zip_path.unlink(missing_ok=True)


async def fetch_source_to_directory(
    repo: RepoInput,
    job_id: UUID,
    *,
    settings: Settings | None = None,
) -> Path:
    """拉取源码并返回代码根目录绝对路径."""
    cfg = settings or get_settings()
    url = repo.effective_source_url()
    if not url:
        raise SourceFetchError("缺少 source_url")

    kind = classify_source_kind(repo)
    assert_host_allowed(url, kind, cfg)

    work = Path(cfg.SOURCE_FETCH_WORKDIR_BASE).resolve() / str(job_id)
    if work.exists():
        await asyncio.to_thread(shutil.rmtree, work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)

    logger.info(
        "source_fetch_start",
        extra={"job_id": str(job_id), "kind": kind, "url": _redact_url_for_log(url)},
    )

    if kind == "zip":
        extract_root = work / "unpacked"
        await asyncio.to_thread(_download_and_unzip, url, work, extract_root, cfg)
        return extract_root.resolve()

    repo_dir = work / "repo"
    await asyncio.to_thread(_git_clone, url, repo.ref, repo_dir, cfg)
    return repo_dir.resolve()


def cleanup_job_source_directory(job_id: UUID, settings: Settings | None = None) -> None:
    cfg = settings or get_settings()
    path = Path(cfg.SOURCE_FETCH_WORKDIR_BASE).resolve() / str(job_id)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
