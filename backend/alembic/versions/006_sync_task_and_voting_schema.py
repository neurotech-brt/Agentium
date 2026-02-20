"""Sync Task and Voting Schema

Revision ID: 006_sync_task_and_voting_schema
Revises: 005_add_deleted_at_column
Create Date: 2026-02-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006_sync_task_and_voting_schema'
down_revision = '005_add_deleted_at_column'
branch_labels = None
depends_on = None

def upgrade():
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # ── 1. Create task_deliberations table ────────────────────────────────────
    if 'task_deliberations' not in existing_tables:
        op.create_table(
            'task_deliberations',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('agentium_id', sa.String(20), unique=True, nullable=False),
            sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id'), nullable=False),
            sa.Column('participating_members', sa.JSON(), nullable=False),
            sa.Column('required_approvals', sa.Integer(), default=2, nullable=False),
            sa.Column('min_quorum', sa.Integer(), default=2),
            sa.Column('status', sa.String(20), server_default='pending', nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
            sa.Column('time_limit_minutes', sa.Integer(), default=30),
            sa.Column('votes_for', sa.Integer(), default=0),
            sa.Column('votes_against', sa.Integer(), default=0),
            sa.Column('votes_abstain', sa.Integer(), default=0),
            sa.Column('final_decision', sa.String(20), nullable=True),
            sa.Column('head_overridden', sa.Boolean(), default=False),
            sa.Column('head_override_reason', sa.Text(), nullable=True),
            sa.Column('head_override_at', sa.DateTime(), nullable=True),
            sa.Column('discussion_thread', sa.JSON(), server_default='[]'),
            sa.Column('is_active', sa.Boolean(), server_default='true'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
        )

    # ── 2. Create task_events table ───────────────────────────────────────────
    if 'task_events' not in existing_tables:
        op.create_table(
            'task_events',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('agentium_id', sa.String(20), unique=True, nullable=False),
            sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id'), nullable=False),
            sa.Column('event_type', sa.String(50), nullable=False),
            sa.Column('actor_id', sa.String(36), nullable=False),
            sa.Column('actor_type', sa.String(20), server_default='system'),
            sa.Column('data', sa.JSON(), server_default='{}'),
            sa.Column('sequence_number', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
        )

    # ── 3. Create task_audit_logs table ───────────────────────────────────────
    if 'task_audit_logs' not in existing_tables:
        op.create_table(
            'task_audit_logs',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('agentium_id', sa.String(20), nullable=False),
            sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id'), nullable=False),
            sa.Column('action', sa.String(50), nullable=False),
            sa.Column('action_details', sa.JSON(), server_default='{}'),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('user_agent', sa.String(200), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
        )

    # ── 4. Create voting_records table ───────────────────────────────────────
    if 'voting_records' not in existing_tables:
        op.create_table(
            'voting_records',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('agentium_id', sa.String(20), unique=True, nullable=False),
            sa.Column('voter_agentium_id', sa.String(10), sa.ForeignKey('agents.agentium_id'), nullable=False),
            sa.Column('period_start', sa.DateTime(), nullable=False),
            sa.Column('period_end', sa.DateTime(), nullable=False),
            sa.Column('total_votes_cast', sa.Integer(), default=0),
            sa.Column('votes_for', sa.Integer(), default=0),
            sa.Column('votes_against', sa.Integer(), default=0),
            sa.Column('votes_abstain', sa.Integer(), default=0),
            sa.Column('votes_changed', sa.Integer(), default=0),
            sa.Column('deliberations_participated', sa.Integer(), default=0),
            sa.Column('deliberations_missed', sa.Integer(), default=0),
            sa.Column('avg_participation_rate', sa.Integer(), default=0),
            sa.Column('proposals_made', sa.Integer(), default=0),
            sa.Column('proposals_accepted', sa.Integer(), default=0),
            sa.Column('is_active', sa.Boolean(), server_default='true'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
        )

    # ── 5. Sync tasks table ──────────────────────────────────────────────────
    existing_tasks_cols = [c['name'] for c in inspector.get_columns('tasks')]
    
    tasks_to_add = [
        ('task_type', sa.Column('task_type', sa.String(50), server_default='execution', nullable=False)),
        ('constitutional_basis', sa.Column('constitutional_basis', sa.Text(), nullable=True)),
        ('hierarchical_id', sa.Column('hierarchical_id', sa.String(100), nullable=True)),
        ('recurrence_pattern', sa.Column('recurrence_pattern', sa.String(100), nullable=True)),
        ('parent_task_id', sa.Column('parent_task_id', sa.String(36), sa.ForeignKey('tasks.id'), nullable=True)),
        ('execution_plan_id', sa.Column('execution_plan_id', sa.String(36), nullable=True)),
        ('is_idle_task', sa.Column('is_idle_task', sa.Boolean(), server_default='false', nullable=False)),
        ('idle_task_category', sa.Column('idle_task_category', sa.String(50), nullable=True)),
        ('estimated_tokens', sa.Column('estimated_tokens', sa.Integer(), server_default='0')),
        ('tokens_used', sa.Column('tokens_used', sa.Integer(), server_default='0')),
        ('status_history', sa.Column('status_history', sa.JSON(), server_default='[]')),
        ('head_of_council_id', sa.Column('head_of_council_id', sa.String(36), sa.ForeignKey('agents.id'), nullable=True)),
        ('assigned_council_ids', sa.Column('assigned_council_ids', sa.JSON(), server_default='[]')),
        ('lead_agent_id', sa.Column('lead_agent_id', sa.String(36), sa.ForeignKey('agents.id'), nullable=True)),
        ('assigned_task_agent_ids', sa.Column('assigned_task_agent_ids', sa.JSON(), server_default='[]')),
        ('requires_deliberation', sa.Column('requires_deliberation', sa.Boolean(), server_default='true')),
        ('deliberation_id', sa.Column('deliberation_id', sa.String(36), nullable=True)),
        ('approved_by_council', sa.Column('approved_by_council', sa.Boolean(), server_default='false')),
        ('approved_by_head', sa.Column('approved_by_head', sa.Boolean(), server_default='false')),
        ('execution_plan', sa.Column('execution_plan', sa.Text(), nullable=True)),
        ('execution_context', sa.Column('execution_context', sa.Text(), nullable=True)),
        ('tools_allowed', sa.Column('tools_allowed', sa.JSON(), server_default='[]')),
        ('sandbox_mode', sa.Column('sandbox_mode', sa.Boolean(), server_default='true')),
        ('result_data', sa.Column('result_data', sa.JSON(), nullable=True)),
        ('result_files', sa.Column('result_files', sa.JSON(), nullable=True)),
        ('completion_percentage', sa.Column('completion_percentage', sa.Integer(), server_default='0')),
        ('due_date', sa.Column('due_date', sa.DateTime(), nullable=True)),
        ('time_estimated', sa.Column('time_estimated', sa.Integer(), server_default='0')),
        ('time_actual', sa.Column('time_actual', sa.Integer(), server_default='0')),
        ('error_count', sa.Column('error_count', sa.Integer(), server_default='0')),
        ('last_error', sa.Column('last_error', sa.Text(), nullable=True)),
        ('retry_count', sa.Column('retry_count', sa.Integer(), server_default='0')),
        ('max_retries', sa.Column('max_retries', sa.Integer(), server_default='5')),
    ]
    
    for col_name, col_def in tasks_to_add:
        if col_name not in existing_tasks_cols:
            op.add_column('tasks', col_def)

    # Add FK constraint for deliberation_id if it doesn't exist
    if 'deliberation_id' in [c['name'] for c in inspector.get_columns('tasks')]:
        try:
            op.create_foreign_key('tasks_deliberation_id_fkey', 'tasks', 'task_deliberations', ['deliberation_id'], ['id'])
        except: pass

    # ── 6. Sync individual_votes table ───────────────────────────────────────
    existing_vote_cols = [c['name'] for c in inspector.get_columns('individual_votes')]
    if 'task_deliberation_id' not in existing_vote_cols:
        op.add_column('individual_votes', sa.Column('task_deliberation_id', sa.String(36), sa.ForeignKey('task_deliberations.id'), nullable=True))
    if 'vote_changed' not in existing_vote_cols:
        op.add_column('individual_votes', sa.Column('vote_changed', sa.Boolean(), server_default='false'))
    if 'original_vote' not in existing_vote_cols:
        op.add_column('individual_votes', sa.Column('original_vote', sa.String(10), nullable=True))
    if 'changed_at' not in existing_vote_cols:
        op.add_column('individual_votes', sa.Column('changed_at', sa.DateTime(), nullable=True))

    # Add CheckConstraint
    try:
        op.execute("ALTER TABLE individual_votes ADD CONSTRAINT check_vote_has_parent CHECK (task_deliberation_id IS NOT NULL OR amendment_voting_id IS NOT NULL)")
    except: pass

    # ── 7. Update amendment_votings ──────────────────────────────────────────
    existing_amendment_cols = [c['name'] for c in inspector.get_columns('amendment_votings')]
    
    if 'constitution_id' in existing_amendment_cols and 'amendment_id' not in existing_amendment_cols:
        op.alter_column('amendment_votings', 'constitution_id', new_column_name='amendment_id')
    
    if 'eligible_voters' not in existing_amendment_cols:
        op.add_column('amendment_votings', sa.Column('eligible_voters', sa.JSON(), server_default='[]'))
    if 'supermajority_threshold' not in existing_amendment_cols:
        op.add_column('amendment_votings', sa.Column('supermajority_threshold', sa.Integer(), server_default='66'))
    if 'final_result' not in existing_amendment_cols:
        op.add_column('amendment_votings', sa.Column('final_result', sa.String(20), nullable=True))
    if 'discussion_thread' not in existing_amendment_cols:
        op.add_column('amendment_votings', sa.Column('discussion_thread', sa.JSON(), server_default='[]'))
    
    if 'votes_required' in existing_amendment_cols and 'required_votes' not in existing_amendment_cols:
        op.alter_column('amendment_votings', 'votes_required', new_column_name='required_votes')
    
    if 'voting_started_at' in existing_amendment_cols and 'started_at' not in existing_amendment_cols:
        op.alter_column('amendment_votings', 'voting_started_at', new_column_name='started_at')
    if 'voting_ended_at' in existing_amendment_cols and 'ended_at' not in existing_amendment_cols:
        op.alter_column('amendment_votings', 'voting_ended_at', new_column_name='ended_at')

def downgrade():
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'voting_records' in existing_tables: op.drop_table('voting_records')
    if 'task_audit_logs' in existing_tables: op.drop_table('task_audit_logs')
    if 'task_events' in existing_tables: op.drop_table('task_events')
    
    if 'task_deliberations' in existing_tables:
        try:
            op.drop_constraint('tasks_deliberation_id_fkey', 'tasks', type_='foreignkey')
        except: pass
        op.drop_table('task_deliberations')

    existing_tasks_cols = [c['name'] for c in inspector.get_columns('tasks')]
    tasks_cols = [
        'task_type', 'constitutional_basis', 'hierarchical_id', 'recurrence_pattern',
        'parent_task_id', 'execution_plan_id', 'is_idle_task', 'idle_task_category',
        'estimated_tokens', 'tokens_used', 'status_history', 'head_of_council_id',
        'assigned_council_ids', 'lead_agent_id', 'assigned_task_agent_ids',
        'requires_deliberation', 'deliberation_id', 'approved_by_council',
        'approved_by_head', 'execution_plan', 'execution_context', 'tools_allowed',
        'sandbox_mode', 'result_data', 'result_files', 'completion_percentage',
        'due_date', 'time_estimated', 'time_actual', 'error_count', 'last_error',
        'retry_count', 'max_retries'
    ]
    for col in tasks_cols:
        if col in existing_tasks_cols:
            op.drop_column('tasks', col)

    try:
        op.execute("ALTER TABLE individual_votes DROP CONSTRAINT check_vote_has_parent")
    except: pass
    
    existing_vote_cols = [c['name'] for c in inspector.get_columns('individual_votes')]
    for col in ['changed_at', 'original_vote', 'vote_changed', 'task_deliberation_id']:
        if col in existing_vote_cols:
            op.drop_column('individual_votes', col)

    existing_amendment_cols = [c['name'] for c in inspector.get_columns('amendment_votings')]
    if 'ended_at' in existing_amendment_cols: op.alter_column('amendment_votings', 'ended_at', new_column_name='voting_ended_at')
    if 'started_at' in existing_amendment_cols: op.alter_column('amendment_votings', 'started_at', new_column_name='voting_started_at')
    if 'required_votes' in existing_amendment_cols: op.alter_column('amendment_votings', 'required_votes', new_column_name='votes_required')
    for col in ['discussion_thread', 'final_result', 'supermajority_threshold', 'eligible_voters']:
        if col in existing_amendment_cols:
            op.drop_column('amendment_votings', col)
    if 'amendment_id' in existing_amendment_cols: op.alter_column('amendment_votings', 'amendment_id', new_column_name='constitution_id')
