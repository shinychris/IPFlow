"""seed nice classification (45 classes) for production

Revision ID: 20260628
Revises: 20260322
Create Date: 2026-06-28 00:00:00.000000

生产环境（Postgres + alembic）下填充商标尼斯分类种子数据。
开发环境由 main.py 的 startup 钩子填充，本 migration 保证生产表非空。
"""

from typing import Sequence, Union
from datetime import datetime
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260628"
down_revision: Union[str, None] = "20260322"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_NAME = "nice_classification"


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in inspect(bind).get_table_names()


def upgrade() -> None:
    # 表不存在（旧库未建表）则跳过，交由 SQLModel 建表迁移处理
    if not _table_exists(TABLE_NAME):
        return

    bind = op.get_bind()

    # 幂等：已有数据则跳过，避免重复插入
    existing = bind.execute(
        sa.text(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    ).scalar()
    if existing and existing > 0:
        return

    # 复用种子数据源，不重复定义 45 类
    from ipflow.db.nice_seed import NICE_CLASSES

    now = datetime.utcnow()
    rows = [
        {
            "id": str(uuid4()),
            "class_number": num,
            "class_name": name_cn,
            "class_name_en": name_en,
            "description": desc,
            # 整数 1 兼容 SQLite 与 Postgres 的 Boolean 列
            "is_active": 1,
            "created_at": now,
            "updated_at": now,
        }
        for num, name_cn, name_en, desc in NICE_CLASSES
    ]

    nice_table = sa.table(
        TABLE_NAME,
        sa.Column("id", sa.String),
        sa.Column("class_number", sa.Integer),
        sa.Column("class_name", sa.String),
        sa.Column("class_name_en", sa.String),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Integer),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )
    op.bulk_insert(nice_table, rows)


def downgrade() -> None:
    if not _table_exists(TABLE_NAME):
        return
    op.execute(f"DELETE FROM {TABLE_NAME}")
