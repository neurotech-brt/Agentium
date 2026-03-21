"""Add last_heartbeat_at column for self-healing crash detection

Revision ID: 010_self_healing
Revises: 009_task_delegation
Create Date: 2026-03-21

What this migration does
─────────────────────────
Phase 13.2 — Self-Healing & Auto-Recovery System

1. Adds `last_heartbeat_at` (DateTime, nullable) to `agents` table.
   Used by the heartbeat Celery beat task (60 s) and crash-detection
   watchdog (30 s) to identify unresponsive agents.

Column is nullable so this migration is safe to run against a live
database without downtime.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '010_self_healing'
down_revision = '009_task_delegation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    print("🚀 Starting migration 010_self_healing ...")

    existing_cols = {
        col['name'] for col in inspector.get_columns('agents')
    }

    if 'last_heartbeat_at' not in existing_cols:
        op.add_column('agents', sa.Column(
            'last_heartbeat_at', sa.DateTime(), nullable=True,
        ))
        op.create_index(
            'ix_agents_last_heartbeat_at',
            'agents', ['last_heartbeat_at'],
        )
        print("  ✅ Added last_heartbeat_at to agents")
    else:
        print("  ℹ️  last_heartbeat_at already exists — skipping")

    print("\n" + "=" * 60)
    print("✅ Migration 010_self_healing completed!")
    print("=" * 60)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    print("🔄 Downgrading migration 010_self_healing ...")

    existing_cols = {
        col['name'] for col in inspector.get_columns('agents')
    }

    if 'last_heartbeat_at' in existing_cols:
        op.drop_index('ix_agents_last_heartbeat_at', table_name='agents')
        op.drop_column('agents', 'last_heartbeat_at')
        print("  ✅ Dropped last_heartbeat_at from agents")

    print("✅ Downgrade 010_self_healing completed.")
