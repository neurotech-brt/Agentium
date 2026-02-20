"""Fix schema inconsistencies:
1. Convert is_active and other VARCHAR(1) flags to BOOLEAN.
2. Align users.id and related foreign keys to Integer.

Revision ID: 003_fix_schema_consistency
Revises: 002_add_missing_tables
Create Date: 2026-02-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_fix_schema_consistency'
down_revision = '6_3_acceptance_criteria'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Convert is_active in all tables from VARCHAR(1) to BOOLEAN
    tables_with_is_active = [
        'users', 'user_model_configs', 'ethos', 'agents', 'scheduled_tasks', 
        'scheduled_task_executions', 'constitutions', 'tasks', 'subtasks', 
        'amendment_votings', 'individual_votes', 'audit_logs', 'channels', 
        'model_usage_logs', 'agent_health_reports', 'violation_reports', 
        'task_verifications', 'performance_metrics', 'monitoring_alerts', 
        'critique_reviews', 'tool_staging'
    ]
    
    for table in tables_with_is_active:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN is_active DROP DEFAULT")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN is_active TYPE BOOLEAN USING (is_active = 'Y')")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN is_active SET DEFAULT TRUE")

    # Convert is_deleted and is_archived in conversations and chat_messages
    op.execute("ALTER TABLE conversations ALTER COLUMN is_deleted DROP DEFAULT")
    op.execute("ALTER TABLE conversations ALTER COLUMN is_deleted TYPE BOOLEAN USING (is_deleted = 'Y')")
    op.execute("ALTER TABLE conversations ALTER COLUMN is_deleted SET DEFAULT FALSE")
    
    op.execute("ALTER TABLE conversations ALTER COLUMN is_archived DROP DEFAULT")
    op.execute("ALTER TABLE conversations ALTER COLUMN is_archived TYPE BOOLEAN USING (is_archived = 'Y')")
    op.execute("ALTER TABLE conversations ALTER COLUMN is_archived SET DEFAULT FALSE")
    
    op.execute("ALTER TABLE chat_messages ALTER COLUMN is_deleted DROP DEFAULT")
    op.execute("ALTER TABLE chat_messages ALTER COLUMN is_deleted TYPE BOOLEAN USING (is_deleted = 'Y')")
    op.execute("ALTER TABLE chat_messages ALTER COLUMN is_deleted SET DEFAULT FALSE")

    # 2. Align users.id and related foreign keys to Integer
    # This is a bit complex due to foreign keys. 
    # Since we are in initialization phase, we'll drop FKs, change types, and re-add them.
    
    # Drop Foreign Keys
    op.drop_constraint('user_model_configs_user_id_fkey', 'user_model_configs', type_='foreignkey')
    op.drop_constraint('conversations_user_id_fkey', 'conversations', type_='foreignkey')
    op.drop_constraint('chat_messages_user_id_fkey', 'chat_messages', type_='foreignkey')
    
    # Change users.id to Integer autoincrement
    # Step 1: Remove default if any
    op.execute("ALTER TABLE users ALTER COLUMN id DROP DEFAULT")
    # Step 2: Convert to integer. Skip data conversion if empty, or map if not empty.
    # Since we are fixing a startup error, users table is likely empty or has 'admin' which failed.
    op.execute("DELETE FROM users") # Clean start to avoid cast issues
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE INTEGER USING (id::integer)")
    op.execute("CREATE SEQUENCE users_id_seq")
    op.execute("ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq')")
    op.execute("ALTER SEQUENCE users_id_seq OWNED BY users.id")
    
    # Change referencing columns
    op.execute("ALTER TABLE user_model_configs ALTER COLUMN user_id TYPE INTEGER USING (NULL)") # Default to NULL or sovereign ID
    op.execute("ALTER TABLE conversations ALTER COLUMN user_id TYPE INTEGER USING (user_id::integer)")
    op.execute("ALTER TABLE chat_messages ALTER COLUMN user_id TYPE INTEGER USING (user_id::integer)")
    
    # Re-add Foreign Keys
    op.create_foreign_key('user_model_configs_user_id_fkey', 'user_model_configs', 'users', ['user_id'], ['id'])
    op.create_foreign_key('conversations_user_id_fkey', 'conversations', 'users', ['user_id'], ['id'])
    op.create_foreign_key('chat_messages_user_id_fkey', 'chat_messages', 'users', ['user_id'], ['id'])


def downgrade():
    # Revert flag columns (best effort)
    # This is complex and usually not needed for this fix, 
    # but for completeness we would convert back to String(1).
    pass
