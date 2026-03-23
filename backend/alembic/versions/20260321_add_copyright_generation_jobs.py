"""add copyright generation jobs and flow fields

Revision ID: 20260321
Revises: 20260316
Create Date: 2026-03-21 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "20260321"
down_revision: Union[str, None] = "20260316"
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
    if not _table_exists("copyright_generation_job"):
        op.create_table(
            "copyright_generation_job",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("job_type", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("current_step", sa.String(length=100), nullable=True),
            sa.Column("input_payload", sa.JSON(), nullable=True),
            sa.Column("result_payload", sa.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_copyright_generation_job_project_id",
            "copyright_generation_job",
            ["project_id"],
            unique=False,
        )
        op.create_index(
            "ix_copyright_generation_job_status",
            "copyright_generation_job",
            ["status"],
            unique=False,
        )
        op.create_index(
            "ix_copyright_generation_job_job_type",
            "copyright_generation_job",
            ["job_type"],
            unique=False,
        )

    if _table_exists("project") and not _column_exists("project", "flow_status"):
        op.add_column("project", sa.Column("flow_status", sa.String(length=30), nullable=True))
        op.create_index("ix_project_flow_status", "project", ["flow_status"], unique=False)

    if _table_exists("copyright_data"):
        if not _column_exists("copyright_data", "source"):
            op.add_column(
                "copyright_data",
                sa.Column("source", sa.String(length=20), nullable=False, server_default="human"),
            )
        if not _column_exists("copyright_data", "revision"):
            op.add_column(
                "copyright_data",
                sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
            )
        if not _column_exists("copyright_data", "is_confirmed"):
            op.add_column(
                "copyright_data",
                sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
        if not _column_exists("copyright_data", "last_edited_by"):
            op.add_column(
                "copyright_data",
                sa.Column("last_edited_by", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                "fk_copyright_data_last_edited_by",
                "copyright_data",
                "user",
                ["last_edited_by"],
                ["id"],
            )

    if _table_exists("copyright_manual"):
        if not _column_exists("copyright_manual", "source"):
            op.add_column(
                "copyright_manual",
                sa.Column("source", sa.String(length=20), nullable=False, server_default="human"),
            )
        if not _column_exists("copyright_manual", "revision"):
            op.add_column(
                "copyright_manual",
                sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
            )
        if not _column_exists("copyright_manual", "is_confirmed"):
            op.add_column(
                "copyright_manual",
                sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
            )
        if not _column_exists("copyright_manual", "last_edited_by"):
            op.add_column(
                "copyright_manual",
                sa.Column("last_edited_by", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                "fk_copyright_manual_last_edited_by",
                "copyright_manual",
                "user",
                ["last_edited_by"],
                ["id"],
            )


def downgrade() -> None:
    if _table_exists("copyright_manual") and _column_exists("copyright_manual", "last_edited_by"):
        op.drop_constraint("fk_copyright_manual_last_edited_by", "copyright_manual", type_="foreignkey")
        op.drop_column("copyright_manual", "last_edited_by")
    if _table_exists("copyright_manual") and _column_exists("copyright_manual", "is_confirmed"):
        op.drop_column("copyright_manual", "is_confirmed")
    if _table_exists("copyright_manual") and _column_exists("copyright_manual", "revision"):
        op.drop_column("copyright_manual", "revision")
    if _table_exists("copyright_manual") and _column_exists("copyright_manual", "source"):
        op.drop_column("copyright_manual", "source")

    if _table_exists("copyright_data") and _column_exists("copyright_data", "last_edited_by"):
        op.drop_constraint("fk_copyright_data_last_edited_by", "copyright_data", type_="foreignkey")
        op.drop_column("copyright_data", "last_edited_by")
    if _table_exists("copyright_data") and _column_exists("copyright_data", "is_confirmed"):
        op.drop_column("copyright_data", "is_confirmed")
    if _table_exists("copyright_data") and _column_exists("copyright_data", "revision"):
        op.drop_column("copyright_data", "revision")
    if _table_exists("copyright_data") and _column_exists("copyright_data", "source"):
        op.drop_column("copyright_data", "source")

    if _table_exists("project") and _column_exists("project", "flow_status"):
        try:
            op.drop_index("ix_project_flow_status", table_name="project")
        except Exception:
            pass
        op.drop_column("project", "flow_status")

    if _table_exists("copyright_generation_job"):
        for idx in [
            "ix_copyright_generation_job_job_type",
            "ix_copyright_generation_job_status",
            "ix_copyright_generation_job_project_id",
        ]:
            try:
                op.drop_index(idx, table_name="copyright_generation_job")
            except Exception:
                pass
        op.drop_table("copyright_generation_job")
