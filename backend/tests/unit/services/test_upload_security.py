"""文件上传安全校验测试（P1-A）.

覆盖：
- 扩展名白名单
- MIME 与扩展名匹配
- 魔数嗅探（伪装扩展名检测）
- 大小限制
"""
# pylint: disable=import-error,redefined-outer-name,unused-argument
from __future__ import annotations

import pytest

from ipflow.services.upload_security import (
    ALLOWED_EXTENSIONS,
    sniff_magic,
    validate_upload,
)


class TestSniffMagic:
    """魔数嗅探."""

    def test_zip(self):
        assert sniff_magic(b"\x50\x4b\x03\x04xxxx") == "zip"

    def test_pdf(self):
        assert sniff_magic(b"%PDF-1.4...") == "pdf"

    def test_png(self):
        assert sniff_magic(b"\x89PNG\r\n\x1a\n...") == "png"

    def test_unknown(self):
        assert sniff_magic(b"plain text content") is None


class TestValidateUpload:
    """三重校验."""

    def test_valid_pdf(self):
        r = validate_upload(
            filename="manual.pdf",
            content_type="application/pdf",
            file_size=1024,
            content_head=b"%PDF-1.4 content",
        )
        assert r.is_valid

    def test_valid_zip(self):
        r = validate_upload(
            filename="code.zip",
            content_type="application/zip",
            file_size=4096,
            content_head=b"\x50\x4b\x03\x04rest",
        )
        assert r.is_valid

    def test_empty_filename(self):
        r = validate_upload(filename="", content_type="application/pdf", file_size=10, content_head=b"%PDF")
        assert not r.is_valid
        assert "文件名" in r.error

    def test_disallowed_extension(self):
        r = validate_upload(
            filename="malware.exe",
            content_type="application/x-msdownload",
            file_size=100,
            content_head=b"MZ",
        )
        assert not r.is_valid
        assert "不支持" in r.error

    def test_zero_size(self):
        r = validate_upload(
            filename="empty.pdf", content_type="application/pdf", file_size=0, content_head=b""
        )
        assert not r.is_valid

    def test_oversize(self, monkeypatch):
        """超过大小限制应拒绝."""
        from ipflow.services import upload_security
        monkeypatch.setattr(upload_security, "get_max_upload_size", lambda: 100)
        r = validate_upload(
            filename="big.pdf",
            content_type="application/pdf",
            file_size=200,
            content_head=b"%PDF",
        )
        assert not r.is_valid
        assert "大小限制" in r.error

    def test_mime_extension_mismatch(self):
        """声明 MIME 与扩展名不符应拒绝."""
        r = validate_upload(
            filename="doc.pdf",
            content_type="application/msword",  # .pdf 不应是 msword
            file_size=100,
            content_head=b"%PDF-1.4",
        )
        assert not r.is_valid
        assert "不匹配" in r.error

    def test_magic_disguise_detected(self):
        """扩展名伪装（.pdf 实为 zip）应被魔数嗅探拦截."""
        r = validate_upload(
            filename="fake.pdf",
            content_type="application/pdf",
            file_size=100,
            content_head=b"\x50\x4b\x03\x04zipcontent",  # 实际是 zip
        )
        assert not r.is_valid
        assert "不符" in r.error

    def test_tar_gz_double_extension(self):
        """.tar.gz 双扩展应被正确识别."""
        r = validate_upload(
            filename="source.tar.gz",
            content_type="application/gzip",
            file_size=1024,
            content_head=b"\x1f\x8bgzip",
        )
        assert r.is_valid

    def test_text_md_no_magic_check(self):
        """纯文本类（.md）无魔数簇，跳过魔数校验应通过."""
        r = validate_upload(
            filename="readme.md",
            content_type="text/markdown",
            file_size=100,
            content_head=b"# Title",
        )
        assert r.is_valid
