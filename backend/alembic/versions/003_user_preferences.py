"""add_user_preferences_table

Revision ID: 003_user_preferences
Revises: 002_mcp_tools
Create Date: 2026-02-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003_user_preferences'
down_revision = '002_mcp_tools'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agentium_id', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),

        # User ownership
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True, index=True),

        # Preference fields
        sa.Column('category', sa.String(50), nullable=False, server_default='general', index=True),
        sa.Column('key', sa.String(255), nullable=False, index=True),
        sa.Column('value_json', sa.Text(), nullable=False),
        sa.Column('data_type', sa.String(20), nullable=False, server_default='string'),
        sa.Column('scope', sa.String(20), nullable=False, server_default='global', index=True),
        sa.Column('scope_target_id', sa.String(20), nullable=True, index=True),

        # Metadata
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_editable_by_agents', sa.String(1), server_default='Y', nullable=False),
        sa.Column('last_modified_by_agent', sa.String(10), nullable=True),
        sa.Column('last_agent_modified_at', sa.DateTime(), nullable=True),
    )

    # Create indexes
    op.create_index('idx_user_pref_user_cat', 'user_preferences', ['user_id', 'category'])
    op.create_index('idx_user_pref_key_scope', 'user_preferences', ['key', 'scope', 'scope_target_id'])
    op.create_index('idx_user_pref_agent_editable', 'user_preferences', ['is_editable_by_agents', 'category'])

    # Create user_preference_history table
    op.create_table(
        'user_preference_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agentium_id', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),

        sa.Column('preference_id', sa.String(36), sa.ForeignKey('user_preferences.id'), nullable=False, index=True),
        sa.Column('previous_value_json', sa.Text(), nullable=False),
        sa.Column('new_value_json', sa.Text(), nullable=False),
        sa.Column('changed_by_agentium_id', sa.String(10), nullable=True),
        sa.Column('changed_by_user_id', sa.String(36), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('change_category', sa.String(50), server_default='manual', nullable=False),
    )

    # Seed default system preferences
    op.execute("""
        INSERT INTO user_preferences (id, agentium_id, category, key, value_json, data_type, scope, description, is_editable_by_agents, created_at, updated_at)
        VALUES
        (gen_random_uuid(), 'PREF0001', 'general', 'system.name', '"Agentium"', 'string', 'system', 'System name displayed in UI', 'N', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0002', 'ui', 'ui.theme', '"dark"', 'string', 'global', 'UI theme (dark/light/auto)', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0003', 'ui', 'ui.language', '"en"', 'string', 'global', 'UI language code', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0004', 'chat', 'chat.history_limit', '50', 'integer', 'global', 'Maximum messages to keep in chat history', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0005', 'chat', 'chat.auto_save', 'true', 'boolean', 'global', 'Auto-save conversations', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0006', 'agents', 'agents.default_timeout', '300', 'integer', 'global', 'Default task timeout in seconds', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0007', 'agents', 'agents.max_concurrent_tasks', '5', 'integer', 'global', 'Maximum concurrent tasks per agent', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0008', 'tasks', 'tasks.auto_archive_days', '30', 'integer', 'global', 'Days after which completed tasks are archived', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0009', 'notifications', 'notifications.enabled', 'true', 'boolean', 'global', 'Enable notifications', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0010', 'notifications', 'notifications.channels', '["websocket", "email"]', 'json', 'global', 'Active notification channels', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0011', 'models', 'models.default_temperature', '0.7', 'float', 'global', 'Default temperature for LLM calls', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0012', 'privacy', 'privacy.data_retention_days', '90', 'integer', 'global', 'Data retention period in days', 'N', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0013', 'tools', 'tools.max_execution_time', '60', 'integer', 'global', 'Maximum tool execution time in seconds', 'Y', NOW(), NOW()),
        (gen_random_uuid(), 'PREF0014', 'tools', 'tools.sandbox_enabled', 'true', 'boolean', 'global', 'Enable sandbox for tool execution', 'N', NOW(), NOW())
        ON CONFLICT (agentium_id) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('user_preference_history')
    op.drop_table('user_preferences')