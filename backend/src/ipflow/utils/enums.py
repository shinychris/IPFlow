"""枚举相关工具函数."""

from enum import Enum
from typing import Any, Optional


def enum_value(value: Any) -> Optional[str]:
    """安全获取枚举的字符串值.

    SQLModel 的枚举列在不同后端可能返回枚举成员或纯字符串：

    - PostgreSQL 原生枚举 → 返回枚举成员（含 ``.value``）
    - SQLite / MySQL 字符串列 → 返回纯字符串（无 ``.value``）

    在序列化为接口响应时统一调用本函数，避免 ``AttributeError``。

    Args:
        value: 枚举成员或纯字符串（可能为 ``None``）

    Returns:
        枚举的字符串值；输入为 ``None`` 时返回 ``None``。

    Examples:
        >>> from ipflow.models.enums import PatentType
        >>> enum_value(PatentType.INVENTION)
        'invention'
        >>> enum_value("invention")
        'invention'
        >>> enum_value(None) is None
        True
    """
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    return str(value)
