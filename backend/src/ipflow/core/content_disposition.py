"""Content-Disposition 头部构造工具.

HTTP 头部要求 latin-1 编码，而中文文件名等非 ASCII 字符无法直接编码，
会触发 ``UnicodeEncodeError``。本工具按 RFC 5987 生成 ASCII 安全的
``Content-Disposition`` 值：同时给出 ASCII 兜底 ``filename`` 与保留原始
名称的 ``filename*``，兼容主流浏览器。
"""

from __future__ import annotations

from urllib.parse import quote


def build_content_disposition(filename: str, *, disposition: str = "attachment") -> str:
    """构造 ASCII 安全的 Content-Disposition 值.

    Args:
        filename: 原始文件名（可含中文等非 ASCII 字符）
        disposition: ``attachment``（默认）或 ``inline``

    Returns:
        形如 ``attachment; filename="fallback.zip"; filename*=UTF-8''%E8%BD%AF%E8%91%97.zip``
    """
    try:
        filename.encode("latin-1")
        ascii_name = filename
    except UnicodeEncodeError:
        # 非 ASCII：用 ASCII 兜底名（保留扩展名），原名放 filename*
        # 仅保留 ASCII 字符，去除后若为空则用 fallback
        ascii_name = "".join(c for c in filename if ord(c) < 128).strip() or "download"
    return (
        f'{disposition}; filename="{ascii_name}"; '
        f"filename*=UTF-8''{quote(filename, safe='')}"
    )
