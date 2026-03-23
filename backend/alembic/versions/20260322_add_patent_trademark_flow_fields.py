"""add patent/trademark draft fields and generic job domain

Revision ID: 20260322
Revises: 20260321
Create Date: 2026-03-22 09:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260322"
down_revision: Union[str, None] = "20260321"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in inspect(bind).get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    columns = inspect(bind).get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def upgrade() -> None:
    if _table_exists("copyright_generation_job"):
        if not _column_exists("copyright_generation_job", "project_type"):
            op.add_column(
                "copyright_generation_job",
                sa.Column("project_type", sa.String(length=20), nullable=False, server_default="copyright"),
            )
            op.create_index(
                "ix_copyright_generation_job_project_type",
                "copyright_generation_job",
                ["project_type"],
                unique=False,
            )
        if not _column_exists("copyright_generation_job", "job_domain"):
            op.add_column(
                "copyright_generation_job",
                sa.Column("job_domain", sa.String(length=20), nullable=False, server_default="copyright"),
            )
            op.create_index(
                "ix_copyright_generation_job_job_domain",
                "copyright_generation_job",
                ["job_domain"],
                unique=False,
            )

    if _table_exists("patent_data"):
        if not _column_exists("patent_data", "source"):
            op.add_column("patent_data", sa.Column("source", sa.String(length=20), nullable=False, server_default="human"))
        if not _column_exists("patent_data", "revision"):
            op.add_column("patent_data", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
        if not _column_exists("patent_data", "is_confirmed"):
            op.add_column("patent_data", sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()))
        if not _column_exists("patent_data", "last_edited_by"):
            op.add_column("patent_data", sa.Column("last_edited_by", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                "fk_patent_data_last_edited_by",
                "patent_data",
                "user",
                ["last_edited_by"],
                ["id"],
            )

    if _table_exists("trademark_data"):
        if not _column_exists("trademark_data", "source"):
            op.add_column(
                "trademark_data",
                sa.Column("source", sa.String(length=20), nullable=False, server_default="human"),
            )
        if not _column_exists("trademark_data", "revision"):
            op.add_column("trademark_data", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
        if not _column_exists("trademark_data", "is_confirmed"):
            op.add_column(
                "trademark_data",
                sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
        if not _column_exists("trademark_data", "last_edited_by"):
            op.add_column("trademark_data", sa.Column("last_edited_by", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                "fk_trademark_data_last_edited_by",
                "trademark_data",
                "user",
                ["last_edited_by"],
                ["id"],
            )


def downgrade() -> None:
    if _table_exists("trademark_data") and _column_exists("trademark_data", "last_edited_by"):
        op.drop_constraint("fk_trademark_data_last_edited_by", "trademark_data", type_="foreignkey")
        op.drop_column("trademark_data", "last_edited_by")
    if _table_exists("trademark_data") and _column_exists("trademark_data", "is_confirmed"):
        op.drop_column("trademark_data", "is_confirmed")
    if _table_exists("trademark_data") and _column_exists("trademark_data", "revision"):
        op.drop_column("trademark_data", "revision")
    if _table_exists("trademark_data") and _column_exists("trademark_data", "source"):
        op.drop_column("trademark_data", "source")

    if _table_exists("patent_data") and _column_exists("patent_data", "last_edited_by"):
        op.drop_constraint("fk_patent_data_last_edited_by", "patent_data", type_="foreignkey")
        op.drop_column("patent_data", "last_edited_by")
    if _table_exists("patent_data") and _column_exists("patent_data", "is_confirmed"):
        op.drop_column("patent_data", "is_confirmed")
    if _table_exists("patent_data") and _column_exists("patent_data", "revision"):
        op.drop_column("patent_data", "revision")
    if _table_exists("patent_data") and _column_exists("patent_data", "source"):
        op.drop_column("patent_data", "source")

    if _table_exists("copyright_generation_job") and _column_exists("copyright_generation_job", "job_domain"):
        try:
            op.drop_index("ix_copyright_generation_job_job_domain", table_name="copyright_generation_job")
        except Exception:
            pass
        op.drop_column("copyright_generation_job", "job_domain")
    if _table_exists("copyright_generation_job") and _column_exists("copyright_generation_job", "project_type"):
        try:
            op.drop_index("ix_copyright_generation_job_project_type", table_name="copyright_generation_job")
        except Exception:
            pass
        op.drop_column("copyright_generation_job", "project_type")
