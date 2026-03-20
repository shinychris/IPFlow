"""add patent/trademark/billing/audit tables

Revision ID: 20260316
Revises: 20250219
Create Date: 2026-03-16 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260316"
down_revision: Union[str, None] = "20250219"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return table_name in inspect(bind).get_table_names()


def upgrade() -> None:
    if not _table_exists("audit_log"):
        op.create_table(
            "audit_log",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("action", sa.String(length=50), nullable=False),
            sa.Column("resource_type", sa.String(length=50), nullable=False),
            sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("old_values", sa.JSON(), nullable=True),
            sa.Column("new_values", sa.JSON(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("request_id", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
            sa.ForeignKeyConstraint(["resource_id"], ["project.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_audit_log_action", "audit_log", ["action"], unique=False)
        op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"], unique=False)
        op.create_index("ix_audit_log_request_id", "audit_log", ["request_id"], unique=False)

    if not _table_exists("plan"):
        op.create_table(
            "plan",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("slug", sa.String(length=50), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price_monthly", sa.Numeric(10, 2), nullable=False),
            sa.Column("price_yearly", sa.Numeric(10, 2), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False),
            sa.Column("features", sa.JSON(), nullable=False),
            sa.Column("limits", sa.JSON(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("is_public", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug"),
        )

    if not _table_exists("subscription"):
        op.create_table(
            "subscription",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("current_period_start", sa.DateTime(), nullable=False),
            sa.Column("current_period_end", sa.DateTime(), nullable=False),
            sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False),
            sa.Column("canceled_at", sa.DateTime(), nullable=True),
            sa.Column("trial_start", sa.DateTime(), nullable=True),
            sa.Column("trial_end", sa.DateTime(), nullable=True),
            sa.Column("payment_provider", sa.String(length=50), nullable=True),
            sa.Column("payment_provider_subscription_id", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
            sa.ForeignKeyConstraint(["plan_id"], ["plan.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_subscription_organization_id", "subscription", ["organization_id"], unique=False)

    if not _table_exists("invoice"):
        op.create_table(
            "invoice",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("amount_due", sa.Numeric(10, 2), nullable=False),
            sa.Column("amount_paid", sa.Numeric(10, 2), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("lines", sa.JSON(), nullable=False),
            sa.Column("payment_provider", sa.String(length=50), nullable=True),
            sa.Column("payment_provider_invoice_id", sa.String(length=255), nullable=True),
            sa.Column("hosted_invoice_url", sa.String(length=500), nullable=True),
            sa.Column("pdf_url", sa.String(length=500), nullable=True),
            sa.Column("paid_at", sa.DateTime(), nullable=True),
            sa.Column("due_date", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
            sa.ForeignKeyConstraint(["subscription_id"], ["subscription.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_invoice_organization_id", "invoice", ["organization_id"], unique=False)

    if not _table_exists("payment_method"):
        op.create_table(
            "payment_method",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("type", sa.String(length=50), nullable=False),
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("provider_payment_method_id", sa.String(length=255), nullable=False),
            sa.Column("last4", sa.String(length=4), nullable=True),
            sa.Column("brand", sa.String(length=50), nullable=True),
            sa.Column("exp_month", sa.Integer(), nullable=True),
            sa.Column("exp_year", sa.Integer(), nullable=True),
            sa.Column("is_default", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_payment_method_organization_id", "payment_method", ["organization_id"], unique=False)

    if not _table_exists("payment_orders"):
        op.create_table(
            "payment_orders",
            sa.Column("id", sa.String(length=255), nullable=False),
            sa.Column("order_no", sa.String(length=64), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("plan_id", sa.String(length=50), nullable=False),
            sa.Column("plan_name", sa.String(length=100), nullable=False),
            sa.Column("billing_interval", sa.String(length=20), nullable=False),
            sa.Column("payment_method", sa.String(length=20), nullable=False),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("transaction_id", sa.String(length=128), nullable=True),
            sa.Column("qr_code", sa.Text(), nullable=True),
            sa.Column("pay_url", sa.Text(), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("paid_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("metadata", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("order_no"),
        )
        op.create_index("ix_payment_orders_order_no", "payment_orders", ["order_no"], unique=True)
        op.create_index("ix_payment_orders_user_id", "payment_orders", ["user_id"], unique=False)

    if not _table_exists("payment_webhook_logs"):
        op.create_table(
            "payment_webhook_logs",
            sa.Column("id", sa.String(length=255), nullable=False),
            sa.Column("payment_id", sa.String(length=255), nullable=True),
            sa.Column("order_no", sa.String(length=64), nullable=True),
            sa.Column("event_id", sa.String(length=128), nullable=False),
            sa.Column("provider", sa.String(length=20), nullable=False),
            sa.Column("payload", sa.Text(), nullable=False),
            sa.Column("success", sa.Boolean(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["payment_id"], ["payment_orders.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("event_id"),
        )
        op.create_index("ix_payment_webhook_logs_event_id", "payment_webhook_logs", ["event_id"], unique=True)
        op.create_index("ix_payment_webhook_logs_order_no", "payment_webhook_logs", ["order_no"], unique=False)

    if not _table_exists("invoices"):
        op.create_table(
            "invoices",
            sa.Column("id", sa.String(length=255), nullable=False),
            sa.Column("payment_id", sa.String(length=255), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("invoice_no", sa.String(length=64), nullable=False),
            sa.Column("type", sa.String(length=20), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("pdf_url", sa.Text(), nullable=True),
            sa.Column("issued_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["payment_id"], ["payment_orders.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("invoice_no"),
        )

    if not _table_exists("patent_data"):
        op.create_table(
            "patent_data",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("patent_type", sa.String(length=20), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("technical_field", sa.Text(), nullable=True),
            sa.Column("background_art", sa.Text(), nullable=True),
            sa.Column("invention_content", sa.JSON(), nullable=True),
            sa.Column("implementation", sa.Text(), nullable=True),
            sa.Column("abstract", sa.Text(), nullable=True),
            sa.Column("abstract_figure_number", sa.String(length=10), nullable=True),
            sa.Column("claims_count", sa.Integer(), nullable=False),
            sa.Column("drawings_count", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("application_number", sa.String(length=50), nullable=True),
            sa.Column("publication_number", sa.String(length=50), nullable=True),
            sa.Column("grant_number", sa.String(length=50), nullable=True),
            sa.Column("filing_date", sa.DateTime(), nullable=True),
            sa.Column("publication_date", sa.DateTime(), nullable=True),
            sa.Column("grant_date", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("project_id"),
        )

    if not _table_exists("patent_claim"):
        op.create_table(
            "patent_claim",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("patent_data_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("claim_number", sa.Integer(), nullable=False),
            sa.Column("claim_type", sa.String(length=20), nullable=False),
            sa.Column("parent_claim_number", sa.Integer(), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["patent_data_id"], ["patent_data.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_patent_claim_patent_data_id", "patent_claim", ["patent_data_id"], unique=False)

    if not _table_exists("patent_drawing"):
        op.create_table(
            "patent_drawing",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("patent_data_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("figure_number", sa.String(length=10), nullable=False),
            sa.Column("figure_title", sa.String(length=200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("upload_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["patent_data_id"], ["patent_data.id"]),
            sa.ForeignKeyConstraint(["upload_id"], ["file_upload.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_patent_drawing_patent_data_id", "patent_drawing", ["patent_data_id"], unique=False)

    if not _table_exists("patent_export_config"):
        op.create_table(
            "patent_export_config",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("patent_data_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("inventor_list", sa.JSON(), nullable=False),
            sa.Column("applicant_info", sa.JSON(), nullable=True),
            sa.Column("agent_info", sa.JSON(), nullable=True),
            sa.Column("priority_claims", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["patent_data_id"], ["patent_data.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("patent_data_id"),
        )

    if not _table_exists("trademark_data"):
        op.create_table(
            "trademark_data",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("trademark_type", sa.String(length=20), nullable=False),
            sa.Column("trademark_name", sa.String(length=200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("design_description", sa.Text(), nullable=True),
            sa.Column("color_claim", sa.Text(), nullable=True),
            sa.Column("upload_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("special_notes", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("application_number", sa.String(length=50), nullable=True),
            sa.Column("registration_number", sa.String(length=50), nullable=True),
            sa.Column("filing_date", sa.DateTime(), nullable=True),
            sa.Column("registration_date", sa.DateTime(), nullable=True),
            sa.Column("expiry_date", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
            sa.ForeignKeyConstraint(["upload_id"], ["file_upload.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("project_id"),
        )

    if not _table_exists("nice_classification"):
        op.create_table(
            "nice_classification",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("class_number", sa.Integer(), nullable=False),
            sa.Column("class_name", sa.String(length=100), nullable=False),
            sa.Column("class_name_en", sa.String(length=200), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_nice_classification_class_number", "nice_classification", ["class_number"], unique=False)

    if not _table_exists("trademark_nice_class"):
        op.create_table(
            "trademark_nice_class",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("trademark_data_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("nice_class_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("goods_services", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["nice_class_id"], ["nice_classification.id"]),
            sa.ForeignKeyConstraint(["trademark_data_id"], ["trademark_data.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_trademark_nice_class_trademark_data_id", "trademark_nice_class", ["trademark_data_id"], unique=False)

    if not _table_exists("trademark_export_config"):
        op.create_table(
            "trademark_export_config",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("trademark_data_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("applicant_info", sa.JSON(), nullable=True),
            sa.Column("priority_claims", sa.JSON(), nullable=True),
            sa.Column("agent_info", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["trademark_data_id"], ["trademark_data.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("trademark_data_id"),
        )


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_trademark_nice_class_trademark_data_id", "trademark_nice_class"),
        ("ix_nice_classification_class_number", "nice_classification"),
        ("ix_patent_drawing_patent_data_id", "patent_drawing"),
        ("ix_patent_claim_patent_data_id", "patent_claim"),
        ("ix_payment_webhook_logs_order_no", "payment_webhook_logs"),
        ("ix_payment_webhook_logs_event_id", "payment_webhook_logs"),
        ("ix_payment_orders_user_id", "payment_orders"),
        ("ix_payment_orders_order_no", "payment_orders"),
        ("ix_payment_method_organization_id", "payment_method"),
        ("ix_invoice_organization_id", "invoice"),
        ("ix_subscription_organization_id", "subscription"),
        ("ix_audit_log_request_id", "audit_log"),
        ("ix_audit_log_created_at", "audit_log"),
        ("ix_audit_log_action", "audit_log"),
    ]:
        try:
            op.drop_index(index_name, table_name=table_name)
        except Exception:
            pass

    for table_name in [
        "trademark_export_config",
        "trademark_nice_class",
        "nice_classification",
        "trademark_data",
        "patent_export_config",
        "patent_drawing",
        "patent_claim",
        "patent_data",
        "invoices",
        "payment_webhook_logs",
        "payment_orders",
        "payment_method",
        "invoice",
        "subscription",
        "plan",
        "audit_log",
    ]:
        if _table_exists(table_name):
            op.drop_table(table_name)
