"""006_wait_poll — create wait_conditions table

Revision ID: 006_wait_poll
Revises: 003
Create Date: 2025-01-01 00:00:00.000000

Non-breaking: adds a new table; no existing columns are modified.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ── Revision identifiers ──────────────────────────────────────────────────────

revision  = "006_wait_poll"
down_revision = "005_speaker_profiles"          
branch_labels = None
depends_on    = None


# ── Enums (created idempotently) ──────────────────────────────────────────────

wait_strategy_enum = postgresql.ENUM(
    "http_poll", "redis_key", "timeout", "webhook", "manual",
    name="waitstrategy",
    create_type=False,
)

wait_condition_status_enum = postgresql.ENUM(
    "pending", "active", "resolved", "expired", "cancelled",
    name="waitconditionstatus",
    create_type=False,
)


def upgrade() -> None:
    # ── Create enum types (safe to re-run) ───────────────────────────────
    op.execute("CREATE TYPE IF NOT EXISTS waitstrategy AS ENUM "
               "('http_poll','redis_key','timeout','webhook','manual')")
    op.execute("CREATE TYPE IF NOT EXISTS waitconditionstatus AS ENUM "
               "('pending','active','resolved','expired','cancelled')")

    # ── Add WAITING to existing taskstatus enum ───────────────────────────
    # ALTER TYPE … ADD VALUE is idempotent in PG 14+ with IF NOT EXISTS.
    op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'waiting'")

    # ── Add WAIT_ENTERED to checkpointphase enum ──────────────────────────
    op.execute("ALTER TYPE checkpointphase ADD VALUE IF NOT EXISTS 'wait_entered'")

    # ── Create wait_conditions table ──────────────────────────────────────
    op.create_table(
        "wait_conditions",

        # BaseEntity columns (mirrors existing pattern)
        sa.Column("id",          sa.String(36),  nullable=False, primary_key=True),
        sa.Column("agentium_id", sa.String(20),  nullable=True,  unique=True),
        sa.Column("created_at",  sa.DateTime(),  nullable=True),
        sa.Column("updated_at",  sa.DateTime(),  nullable=True),
        sa.Column("is_active",   sa.Boolean(),   nullable=True,  server_default="true"),

        # Domain columns
        sa.Column("task_id", sa.String(36),
                  sa.ForeignKey("tasks.id", ondelete="CASCADE"),
                  nullable=False, index=True),

        sa.Column("strategy", sa.Enum(
            "http_poll", "redis_key", "timeout", "webhook", "manual",
            name="waitstrategy",
        ), nullable=False),

        sa.Column("status", sa.Enum(
            "pending", "active", "resolved", "expired", "cancelled",
            name="waitconditionstatus",
        ), nullable=False, server_default="pending"),

        sa.Column("config",               postgresql.JSON(), nullable=False,
                  server_default="'{}'::json"),
        sa.Column("max_attempts",         sa.Integer(), nullable=False, server_default="60"),
        sa.Column("attempt_count",        sa.Integer(), nullable=False, server_default="0"),
        sa.Column("poll_interval_seconds",sa.Integer(), nullable=False, server_default="30"),
        sa.Column("expires_at",           sa.DateTime(), nullable=True),
        sa.Column("resolved_at",          sa.DateTime(), nullable=True),
        sa.Column("resolution_data",      postgresql.JSON(), nullable=True),
        sa.Column("failure_reason",       sa.Text(), nullable=True),
        sa.Column("created_by_agent_id",  sa.String(36), nullable=True),
    )

    # ── Indexes ───────────────────────────────────────────────────────────
    op.create_index("ix_wait_conditions_task_id", "wait_conditions", ["task_id"])
    op.create_index("ix_wait_conditions_status",  "wait_conditions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_wait_conditions_status",  table_name="wait_conditions")
    op.drop_index("ix_wait_conditions_task_id", table_name="wait_conditions")
    op.drop_table("wait_conditions")

    # Note: we intentionally do NOT remove 'waiting' from taskstatus or
    # 'wait_entered' from checkpointphase on downgrade — enum value removal
    # requires table rewrites and is almost never safe in production.
    op.execute("DROP TYPE IF EXISTS waitconditionstatus")
    op.execute("DROP TYPE IF EXISTS waitstrategy")