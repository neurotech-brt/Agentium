"""
Add notification_preferences table (Phase 11.4)

Revision ID: 006_notification_preferences
Revises: 005_phase11_ecosystem
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '006_notification_preferences'
down_revision = '005_phase11_ecosystem'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    print("🚀 Starting migration 006_notification_preferences...")

    if 'notification_preferences' not in existing_tables:
        op.create_table(
            'notification_preferences',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
            sa.Column('votes_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('alerts_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('tasks_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('constitutional_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('quiet_hours_start', sa.String(5), nullable=True),
            sa.Column('quiet_hours_end', sa.String(5), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'])
        print("  ✅ Created notification_preferences table")

    # Also add is_active column to device_tokens if missing (align with model)
    if 'device_tokens' in existing_tables:
        dt_columns = {col['name'] for col in inspector.get_columns('device_tokens')}
        if 'is_active' not in dt_columns:
            op.add_column('device_tokens', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
            print("  ✅ Added device_tokens.is_active")

    print("\n" + "=" * 70)
    print("✅ Migration 006_notification_preferences completed successfully!")
    print("=" * 70)


def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    print("🔄 Starting downgrade of 006_notification_preferences...")

    if 'notification_preferences' in existing_tables:
        op.drop_table('notification_preferences')

    print("✅ Downgrade 006_notification_preferences completed")
