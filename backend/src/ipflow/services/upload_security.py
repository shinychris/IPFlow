"""文件上传安全校验.

防止上传可执行文件、伪装扩展名文件、超大文件等。采用「三重校验」：

1. **扩展名白名单**：``.jpg/.png/.pdf/.zip`` 等业务所需类型
2. **MIME 白名单**：与扩展名匹配的 MIME 列表
3. **魔数嗅探**：读取文件头字节判断真实类型，防止扩展名伪装

同时强制 ``MAX_UPLOAD_SIZE`` 限制单文件大小。
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from ipflow.config import get_settings

logger = logging.getLogger(__name__)

# 允许的文件扩展名 → MIME 映射（业务场景：代码包/证明材料/说明书/图样）
ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    # 代码包
    ".zip": {"application/zip", "application/x-zip-compressed"},
    ".tar": {"application/x-tar"},
    ".tar.gz": {"application/gzip", "application/x-gzip"},
    ".tgz": {"application/gzip", "application/x-gzip"},
    # 文档
    ".pdf": {"application/pdf"},
    ".doc": {"application/msword"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain"},
    # 图片
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".gif": {"image/gif"},
    ".webp": {"image/webp"},
    ".svg": {"image/svg+xml"},
    # 数据
    ".json": {"application/json"},
    ".csv": {"text/csv"},
}

# 文件魔数（前 N 字节签名）→ 推断真实类型
MAGIC_NUMBERS: list[tuple[bytes, str]] = [
    (b"\x50\x4b\x03\x04", "zip"),           # ZIP / DOCX
    (b"\x1f\x8b", "gzip"),                  # GZIP
    (b"%PDF", "pdf"),                        # PDF
    (b"\xff\xd8\xff", "jpg"),               # JPEG
    (b"\x89PNG\r\n\x1a\n", "png"),          # PNG
    (b"GIF87a", "gif"),                      # GIF
    (b"GIF89a", "gif"),                      # GIF
]

# 扩展名簇 → 魔数类型集合（用于交叉校验）
_EXT_MAGIC_CLUSTER: dict[str, set[str]] = {
    ".zip": {"zip"},
    ".docx": {"zip"},  # docx 是 zip 容器
    ".tar.gz": {"gzip"},
    ".tgz": {"gzip"},
    ".pdf": {"pdf"},
    ".jpg": {"jpg"},
    ".jpeg": {"jpg"},
    ".png": {"png"},
    ".gif": {"gif"},
}


@dataclass
class UploadValidationResult:
    """上传校验结果."""

    is_valid: bool
    error: Optional[str] = None
    detected_type: Optional[str] = None


def get_max_upload_size() -> int:
    """获取最大上传字节数（默认 50MB）."""
    settings = get_settings()
    return getattr(settings, "MAX_UPLOAD_SIZE", 50 * 1024 * 1024)


def _get_extension(filename: Optional[str]) -> str:
    """提取小写扩展名（支持 .tar.gz 双扩展）."""
    if not filename:
        return ""
    name = filename.lower().rstrip("/")
    if name.endswith(".tar.gz"):
        return ".tar.gz"
    return os.path.splitext(name)[1]


def sniff_magic(content_head: bytes) -> Optional[str]:
    """通过文件头魔数推断真实类型.

    Args:
        content_head: 文件前若干字节（建议至少 8 字节）

    Returns:
        类型标识（zip/gzip/pdf/jpg/png/gif）或 None（未知/纯文本类）
    """
    for magic, type_name in MAGIC_NUMBERS:
        if content_head.startswith(magic):
            return type_name
    return None


def validate_upload(
    filename: Optional[str],
    content_type: Optional[str],
    file_size: int,
    content_head: bytes,
) -> UploadValidationResult:
    """三重校验上传文件.

    Args:
        filename: 原始文件名
        content_type: 客户端声明的 MIME
        file_size: 文件大小（字节）
        content_head: 文件头字节（用于魔数嗅探，建议前 16 字节）

    Returns:
        ``UploadValidationResult``，``is_valid=False`` 时 ``error`` 说明原因
    """
    # 1. 文件名必须存在且非空
    if not filename or not filename.strip():
        return UploadValidationResult(is_valid=False, error="文件名为空")

    # 2. 大小限制
    max_size = get_max_upload_size()
    if file_size <= 0:
        return UploadValidationResult(is_valid=False, error="文件为空")
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return UploadValidationResult(
            is_valid=False,
            error=f"文件超过大小限制 {max_mb:.0f}MB",
        )

    # 3. 扩展名白名单
    ext = _get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return UploadValidationResult(
            is_valid=False,
            error=f"不支持的文件类型: {ext or '(无扩展名)'}",
        )

    # 4. MIME 白名单（客户端声明值应在白名单内；宽松匹配，允许 charset 等参数）
    declared_mime = (content_type or "").split(";")[0].strip().lower()
    allowed_mimes = ALLOWED_EXTENSIONS[ext]
    if declared_mime and declared_mime not in allowed_mimes:
        return UploadValidationResult(
            is_valid=False,
            error=f"文件 MIME 类型 {declared_mime} 与扩展名 {ext} 不匹配",
        )

    # 5. 魔数交叉校验（仅对有魔数簇的扩展名校验，纯文本类跳过）
    expected_magic_types = _EXT_MAGIC_CLUSTER.get(ext)
    if expected_magic_types:
        detected = sniff_magic(content_head)
        if detected is not None and detected not in expected_magic_types:
            logger.warning(
                "上传文件魔数校验失败：filename=%s ext=%s declared=%s detected=%s",
                filename, ext, declared_mime, detected,
            )
            return UploadValidationResult(
                is_valid=False,
                error=f"文件内容与扩展名 {ext} 不符（检测为 {detected}）",
                detected_type=detected,
            )

    return UploadValidationResult(is_valid=True, detected_type=ext)
