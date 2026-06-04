"""initial

Revision ID: 001
Revises:
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("api_keys",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("key_hash", sa.String(128), unique=True, nullable=False),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table("browsing_tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("api_key_id", sa.String(), nullable=False),
        sa.Column("task", sa.String(), nullable=False),
        sa.Column("start_url", sa.String(), nullable=False),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("result", sa.String(), nullable=True),
        sa.Column("structured_result", sa.JSON(), nullable=True),
        sa.Column("structured_output_status", sa.String(20), server_default="not_requested"),
        sa.Column("trajectory", sa.JSON(), nullable=True),
        sa.Column("agent", sa.String(255), nullable=True),
        sa.Column("max_steps", sa.Integer(), server_default="20"),
        sa.Column("require_auth", sa.Boolean(), server_default="false"),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("webhook_url", sa.String(), nullable=True),
        sa.Column("webhook_format", sa.String(20), server_default="sentinel"),
        sa.Column("rejection_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table("research_tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("api_key_id", sa.String(), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("mode", sa.String(10), server_default="deep"),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("result", sa.String(), nullable=True),
        sa.Column("structured_result", sa.JSON(), nullable=True),
        sa.Column("structured_output_status", sa.String(20), server_default="not_requested"),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("webhook_url", sa.String(), nullable=True),
        sa.Column("webhook_format", sa.String(20), server_default="sentinel"),
        sa.Column("skip_email", sa.Boolean(), server_default="true"),
        sa.Column("user_timezone", sa.String(64), server_default="America/Los_Angeles"),
        sa.Column("user_location", sa.String(255), server_default="San Francisco, CA, US"),
        sa.Column("view_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table("scouts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("api_key_id", sa.String(), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("output_interval", sa.Integer(), server_default="86400"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("is_public", sa.Boolean(), server_default="false"),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("webhook_url", sa.String(), nullable=True),
        sa.Column("webhook_format", sa.String(20), server_default="sentinel"),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_timezone", sa.String(64), server_default="America/Los_Angeles"),
        sa.Column("user_location", sa.String(255), server_default="San Francisco, CA, US"),
        sa.Column("skip_email", sa.Boolean(), server_default="true"),
    )
    op.create_table("scout_updates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("scout_id", sa.String(), sa.ForeignKey("scouts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("structured_result", sa.JSON(), nullable=True),
        sa.Column("structured_output_status", sa.String(20), server_default="not_requested"),
        sa.Column("stats", sa.JSON(), nullable=True),
        sa.Column("header_image_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table("scout_subscriptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("scout_id", sa.String(), sa.ForeignKey("scouts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("scout_subscriptions")
    op.drop_table("scout_updates")
    op.drop_table("scouts")
    op.drop_table("research_tasks")
    op.drop_table("browsing_tasks")
    op.drop_table("api_keys")
