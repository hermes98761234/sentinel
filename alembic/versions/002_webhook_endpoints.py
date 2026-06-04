"""webhook endpoints

Revision ID: 002
Revises: 001
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("webhook_endpoints",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("api_key_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("secret", sa.String(64), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("webhook_format", sa.String(20), server_default="sentinel"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table("webhook_deliveries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("endpoint_id", sa.String(), sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("attempts", sa.Integer(), server_default="0"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_endpoints")
