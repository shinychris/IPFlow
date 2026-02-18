"""基础模型模块.

提供 SQLModel 基类，用于 Alembic 迁移和表创建。
"""

from sqlmodel import SQLModel

# 导出 SQLModel 基类，用于 metadata
__all__ = ["SQLModel"]
