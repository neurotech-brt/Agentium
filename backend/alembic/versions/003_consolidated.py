"""Consolidated Migration: 003 through 011

Revision ID: 003_consolidated
Revises: 002_migration
Create Date: 2026-03-21

What this migration does
─────────────────────────
Merges migrations 003_migration … 011_fix_workflow into a single idempotent file.
All changes are nullable / have server defaults so this is safe against a live DB.

Internal sections (in upgrade order):
  [A]  003-migration/003  reasoning_traces, reasoning_steps; tasks.latest_trace_id
  [B]  003-migration/004  Chat performance indexes
  [C]  003-migration/005  Phase 11 Ecosystem — RBAC on users, delegations,
                          federated_instances (incl. signing_key), federated_tasks,
                          federated_votes, plugins, plugin_installations,
                          plugin_reviews, device_tokens (incl. is_active)
  [D]  003-migration/006  notification_preferences; device_tokens.is_active backfill
  [E]  003-migration/007  audit_logs.screenshot_url; critique_reviews.learning_extracted
  [F]  003-migration/008  federated_instances.signing_key back-fill (idempotent)
  [G]  003-migration/009  experiments, experiment_runs, experiment_results,
                          model_performance_cache + indexes + schema hardening
  [H]  004_webhooks       webhook_subscriptions, webhook_delivery_logs
  [I]  005_models         Composite index on user_model_configs(user_id, is_default)
  [J]  006_workflow +     workflow_executions (FINAL schema — no unique on workflow_id,
       011_fix_workflow    FK → workflows.id, correct columns); workflow_subtasks
                          (FK → workflows.id, BaseEntity columns); tasks new columns
  [K]  007_improvements   audit_logs.actor_id VARCHAR(10→100); users.last_login_at
  [L]  008_skills         skills.description column (table created by 002_migration);
                          skill_submissions (idempotent)
  [M]  009_task_delegation task_dependencies; tasks complexity/delegation columns
  [N]  010_self_healing   agents.last_heartbeat_at
"""

import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.engine.reflection import Inspector

revision = '003_consolidated'
down_revision = '002_migration'
branch_labels = None
depends_on = None


# ── helpers ───────────────────────────────────────────────────────────────────

def _col_names(inspector: Inspector, table: str):
    return {col['name'] for col in inspector.get_columns(table)}

def _index_exists(inspector: Inspector, table: str, index_name: str) -> bool:
    return any(idx['name'] == index_name for idx in inspector.get_indexes(table))

def _constraint_exists(inspector: Inspector, table: str, name: str) -> bool:
    try:
        return any(uc.get('name') == name for uc in inspector.get_unique_constraints(table))
    except Exception:
        return False

def _fk_names(inspector: Inspector, table: str):
    return {fk.get('name') for fk in inspector.get_foreign_keys(table)}


# ── upgrade ───────────────────────────────────────────────────────────────────

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    print("🚀 Starting consolidated migration 003_consolidated ...")

    # =========================================================================
    # [A] Reasoning Traces (003-migration/003)
    # =========================================================================
    print("\n--- [A] Reasoning Traces ---")

    if 'reasoning_traces' not in existing_tables:
        op.create_table(
            'reasoning_traces',
            sa.Column('id',          sa.String(36),  primary_key=True),
            sa.Column('agentium_id', sa.String(20),  unique=True, nullable=False),
            sa.Column('is_active',   sa.Boolean(),   nullable=False, server_default='true'),
            sa.Column('created_at',  sa.DateTime(),  nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at',  sa.DateTime(),  nullable=False, server_default=sa.func.now()),
            sa.Column('deleted_at',  sa.DateTime(),  nullable=True),
            sa.Column('trace_id',    sa.String(64),  nullable=False),
            sa.Column('task_id',     sa.String(64),  nullable=False),
            sa.Column('agent_id',    sa.String(32),  nullable=False),
            sa.Column('agent_tier',  sa.Integer(),   nullable=False, server_default='3'),
            sa.Column('incarnation', sa.Integer(),   nullable=False, server_default='1'),
            sa.Column('goal',          sa.Text(), nullable=False),
            sa.Column('goal_restated', sa.Text(), nullable=True),
            sa.Column('plan',            sa.JSON(), nullable=True),
            sa.Column('skills_used',     sa.JSON(), nullable=True),
            sa.Column('context_summary', sa.Text(), nullable=True),
            sa.Column('current_phase',     sa.String(32), nullable=False,
                      server_default='goal_interpretation'),
            sa.Column('final_outcome',     sa.String(16), nullable=True),
            sa.Column('failure_reason',    sa.Text(),     nullable=True),
            sa.Column('validation_passed', sa.Boolean(),  nullable=True),
            sa.Column('validation_notes',  sa.Text(),     nullable=True),
            sa.Column('total_tokens',      sa.Integer(), nullable=False, server_default='0'),
            sa.Column('total_duration_ms', sa.Float(),   nullable=False, server_default='0.0'),
            sa.Column('started_at',        sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column('completed_at',      sa.DateTime(), nullable=True),
        )
        op.create_index('ix_reasoning_traces_trace_id',   'reasoning_traces', ['trace_id'],       unique=True)
        op.create_index('ix_reasoning_traces_task_id',    'reasoning_traces', ['task_id'])
        op.create_index('ix_reasoning_traces_agent_id',   'reasoning_traces', ['agent_id'])
        op.create_index('ix_reasoning_traces_outcome',    'reasoning_traces', ['final_outcome'])
        op.create_index('ix_reasoning_traces_phase',      'reasoning_traces', ['current_phase'])
        op.create_index('ix_reasoning_traces_created_at', 'reasoning_traces', ['created_at'])
        op.create_index('ix_reasoning_traces_validation', 'reasoning_traces', ['validation_passed'])
        print("  ✅ Created reasoning_traces")
    else:
        print("  ℹ️  reasoning_traces already exists")

    if 'reasoning_steps' not in existing_tables:
        op.create_table(
            'reasoning_steps',
            sa.Column('id',          sa.String(36), primary_key=True),
            sa.Column('agentium_id', sa.String(20), unique=True, nullable=False),
            sa.Column('is_active',   sa.Boolean(),  nullable=False, server_default='true'),
            sa.Column('created_at',  sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at',  sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('deleted_at',  sa.DateTime(), nullable=True),
            sa.Column('trace_id',    sa.String(64),
                      sa.ForeignKey('reasoning_traces.trace_id', ondelete='CASCADE'),
                      nullable=False),
            sa.Column('step_id',   sa.String(80), nullable=False),
            sa.Column('phase',     sa.String(32), nullable=False),
            sa.Column('sequence',  sa.Integer(),  nullable=False),
            sa.Column('description',  sa.Text(),  nullable=False),
            sa.Column('rationale',    sa.Text(),  nullable=False),
            sa.Column('alternatives', sa.JSON(),  nullable=True),
            sa.Column('inputs',       sa.JSON(),  nullable=True),
            sa.Column('outputs',      sa.JSON(),  nullable=True),
            sa.Column('outcome',      sa.String(16), nullable=False, server_default='pending'),
            sa.Column('error',        sa.Text(),     nullable=True),
            sa.Column('tokens_used',  sa.Integer(),  nullable=False, server_default='0'),
            sa.Column('duration_ms',  sa.Float(),    nullable=False, server_default='0.0'),
            sa.Column('started_at',   sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
        )
        op.create_index('ix_reasoning_steps_step_id',           'reasoning_steps', ['step_id'],            unique=True)
        op.create_index('ix_reasoning_steps_trace_id',          'reasoning_steps', ['trace_id'])
        op.create_index('ix_reasoning_steps_phase',             'reasoning_steps', ['phase'])
        op.create_index('ix_reasoning_steps_outcome',           'reasoning_steps', ['outcome'])
        op.create_index('ix_reasoning_steps_trace_id_sequence', 'reasoning_steps', ['trace_id', 'sequence'])
        print("  ✅ Created reasoning_steps")
    else:
        print("  ℹ️  reasoning_steps already exists")

    inspector = Inspector.from_engine(conn)
    task_cols = _col_names(inspector, 'tasks')
    if 'latest_trace_id' not in task_cols:
        op.add_column('tasks', sa.Column('latest_trace_id', sa.String(64), nullable=True))
        print("  ✅ Added tasks.latest_trace_id")
    else:
        print("  ℹ️  tasks.latest_trace_id already exists")

    # Update db_maintenance_config ANALYZE list if present
    try:
        row = conn.execute(text(
            "SELECT config_value FROM db_maintenance_config WHERE config_key = 'analyze_tables'"
        )).fetchone()
        if row:
            current = json.loads(row[0])
            added = [t for t in ('reasoning_traces', 'reasoning_steps') if t not in current]
            if added:
                current.extend(added)
                conn.execute(text(
                    "UPDATE db_maintenance_config SET config_value = :val, updated_at = NOW() "
                    "WHERE config_key = 'analyze_tables'"
                ), {"val": json.dumps(current)})
                print(f"  ✅ Extended db_maintenance_config ANALYZE list: {added}")
    except Exception as exc:
        print(f"  ℹ️  Could not update db_maintenance_config: {exc}")

    # =========================================================================
    # [B] Chat performance indexes (003-migration/004)
    # =========================================================================
    print("\n--- [B] Chat Performance Indexes ---")

    inspector = Inspector.from_engine(conn)

    for idx_name, table, columns, kwargs in [
        ('idx_chat_messages_user_created',  'chat_messages',  ['user_id',         sa.text('created_at DESC')],                    {'postgresql_using': 'btree'}),
        ('idx_chat_messages_conversation',  'chat_messages',  ['conversation_id', sa.text('created_at DESC')],                    {'postgresql_using': 'btree'}),
        ('idx_conversations_user_last_msg', 'conversations',  ['user_id',         sa.text('last_message_at DESC')],               {'postgresql_using': 'btree'}),
        ('idx_conversations_user_active',   'conversations',  ['user_id', 'is_deleted', 'is_archived'],                           {'postgresql_using': 'btree'}),
    ]:
        if not _index_exists(inspector, table, idx_name):
            op.create_index(idx_name, table, columns, unique=False, **kwargs)
            print(f"  ✅ Created {idx_name}")
        else:
            print(f"  ℹ️  {idx_name} already exists")

    # =========================================================================
    # [C] Phase 11 Ecosystem — RBAC, federation, plugins, device_tokens
    #     (003-migration/005 + 008 signing_key merged in)
    # =========================================================================
    print("\n--- [C] Phase 11 Ecosystem ---")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())
    user_cols = _col_names(inspector, 'users')

    if 'role' not in user_cols:
        op.add_column('users', sa.Column('role', sa.String(30), nullable=False, server_default='observer'))
        print("  ✅ Added users.role")
    else:
        print("  ℹ️  users.role already exists")

    if 'delegated_by_id' not in user_cols:
        op.add_column('users', sa.Column('delegated_by_id', sa.String(36), nullable=True))
        op.create_foreign_key('fk_users_delegated_by_id', 'users', 'users', ['delegated_by_id'], ['id'])
        print("  ✅ Added users.delegated_by_id")
    else:
        print("  ℹ️  users.delegated_by_id already exists")

    if 'role_expires_at' not in user_cols:
        op.add_column('users', sa.Column('role_expires_at', sa.DateTime(timezone=True), nullable=True))
        print("  ✅ Added users.role_expires_at")
    else:
        print("  ℹ️  users.role_expires_at already exists")

    if 'delegations' not in existing_tables:
        op.create_table(
            'delegations',
            sa.Column('id',          sa.String(36), primary_key=True),
            sa.Column('grantor_id',  sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('grantee_id',  sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('capabilities',  sa.JSON(),    nullable=False),
            sa.Column('reason',        sa.String(500), nullable=True),
            sa.Column('granted_at',    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('expires_at',    sa.DateTime(timezone=True), nullable=True),
            sa.Column('revoked_at',    sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_emergency',  sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at',    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at',    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active',     sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at',    sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index('ix_delegations_grantor_id', 'delegations', ['grantor_id'])
        op.create_index('ix_delegations_grantee_id', 'delegations', ['grantee_id'])
        print("  ✅ Created delegations")
    else:
        print("  ℹ️  delegations already exists")

    if 'federated_instances' not in existing_tables:
        op.create_table(
            'federated_instances',
            sa.Column('id',                  sa.String(36),  primary_key=True),
            sa.Column('name',                sa.String(100), nullable=False),
            sa.Column('base_url',            sa.String(255), nullable=False, unique=True),
            sa.Column('shared_secret_hash',  sa.String(255), nullable=False),
            sa.Column('status',              sa.String(20),  nullable=False, server_default='pending'),
            sa.Column('trust_level',         sa.String(20),  nullable=False, server_default='limited'),
            sa.Column('capabilities_shared', sa.JSON(),      nullable=True),
            sa.Column('registered_at',       sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('last_heartbeat_at',   sa.DateTime(timezone=True), nullable=True),
            # signing_key included upfront (was added by 008) — no ALTER TABLE needed
            sa.Column('signing_key',         sa.String(255), nullable=True),
            sa.Column('created_at',          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at',          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active',           sa.Boolean(),   server_default='true', nullable=False),
            sa.Column('deleted_at',          sa.DateTime(timezone=True), nullable=True),
        )
        print("  ✅ Created federated_instances (incl. signing_key)")
    else:
        print("  ℹ️  federated_instances already exists")

    if 'federated_tasks' not in existing_tables:
        op.create_table(
            'federated_tasks',
            sa.Column('id',                  sa.String(36), primary_key=True),
            sa.Column('source_instance_id',  sa.String(36), sa.ForeignKey('federated_instances.id'), nullable=True),
            sa.Column('target_instance_id',  sa.String(36), sa.ForeignKey('federated_instances.id'), nullable=True),
            sa.Column('original_task_id',    sa.String(36), nullable=False),
            sa.Column('local_task_id',       sa.String(36), sa.ForeignKey('tasks.id'), nullable=True),
            sa.Column('status',              sa.String(20), nullable=False, server_default='pending'),
            sa.Column('delegated_at',        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('completed_at',        sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at',          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at',          sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active',           sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at',          sa.DateTime(timezone=True), nullable=True),
        )
        print("  ✅ Created federated_tasks")
    else:
        print("  ℹ️  federated_tasks already exists")

    if 'federated_votes' not in existing_tables:
        op.create_table(
            'federated_votes',
            sa.Column('id',                      sa.String(36), primary_key=True),
            sa.Column('proposal_id',             sa.String(36), nullable=False),
            sa.Column('participating_instances', sa.JSON(),     nullable=True),
            sa.Column('votes',                   sa.JSON(),     nullable=True),
            sa.Column('status',                  sa.String(20), nullable=False, server_default='open'),
            sa.Column('closes_at',               sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at',              sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at',              sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active',               sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at',              sa.DateTime(timezone=True), nullable=True),
        )
        print("  ✅ Created federated_votes")
    else:
        print("  ℹ️  federated_votes already exists")

    if 'plugins' not in existing_tables:
        op.create_table(
            'plugins',
            sa.Column('id',                   sa.String(36),  primary_key=True),
            sa.Column('name',                 sa.String(100), nullable=False, unique=True),
            sa.Column('description',          sa.Text(),      nullable=False),
            sa.Column('author',               sa.String(100), nullable=False),
            sa.Column('version',              sa.String(20),  nullable=False),
            sa.Column('plugin_type',          sa.String(50),  nullable=False),
            sa.Column('source_url',           sa.String(255), nullable=True),
            sa.Column('is_verified',          sa.Boolean(),   nullable=False, server_default='false'),
            sa.Column('verification_date',    sa.DateTime(timezone=True), nullable=True),
            sa.Column('install_count',        sa.Integer(),   nullable=False, server_default='0'),
            sa.Column('rating',               sa.Float(),     nullable=False, server_default='0.0'),
            sa.Column('revenue_share_percent',sa.Float(),     nullable=False, server_default='0.0'),
            sa.Column('config_schema',        sa.JSON(),      nullable=True),
            sa.Column('entry_point',          sa.String(255), nullable=False),
            sa.Column('dependencies',         sa.JSON(),      nullable=True),
            sa.Column('status',               sa.String(20),  nullable=False, server_default='draft'),
            sa.Column('submitted_at',         sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('published_at',         sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at',           sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at',           sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active',            sa.Boolean(),   server_default='true', nullable=False),
            sa.Column('deleted_at',           sa.DateTime(timezone=True), nullable=True),
        )
        print("  ✅ Created plugins")
    else:
        print("  ℹ️  plugins already exists")

    if 'plugin_installations' not in existing_tables:
        op.create_table(
            'plugin_installations',
            sa.Column('id',           sa.String(36),  primary_key=True),
            sa.Column('plugin_id',    sa.String(36),  sa.ForeignKey('plugins.id', ondelete='CASCADE'), nullable=False),
            sa.Column('instance_id',  sa.String(100), nullable=False, server_default='local'),
            sa.Column('config',       sa.JSON(),      nullable=True),
            sa.Column('installed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('created_at',   sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at',   sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active',    sa.Boolean(),   server_default='true', nullable=False),
            sa.Column('deleted_at',   sa.DateTime(timezone=True), nullable=True),
        )
        print("  ✅ Created plugin_installations")
    else:
        print("  ℹ️  plugin_installations already exists")

    if 'plugin_reviews' not in existing_tables:
        op.create_table(
            'plugin_reviews',
            sa.Column('id',          sa.String(36),  primary_key=True),
            sa.Column('plugin_id',   sa.String(36),  sa.ForeignKey('plugins.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id',     sa.String(36),  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('rating',      sa.Integer(),   nullable=False),
            sa.Column('review_text', sa.String(1000),nullable=True),
            sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active',   sa.Boolean(),   server_default='true', nullable=False),
            sa.Column('deleted_at',  sa.DateTime(timezone=True), nullable=True),
        )
        print("  ✅ Created plugin_reviews")
    else:
        print("  ℹ️  plugin_reviews already exists")

    # device_tokens — is_active included upfront (was a separate backfill in 006)
    if 'device_tokens' not in existing_tables:
        op.create_table(
            'device_tokens',
            sa.Column('id',            sa.String(36),  primary_key=True),
            sa.Column('user_id',       sa.String(36),  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('platform',      sa.String(20),  nullable=False),
            sa.Column('token',         sa.String(255), nullable=False, unique=True),
            sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('last_used_at',  sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active',     sa.Boolean(),   nullable=False, server_default='true'),
            sa.Column('created_at',    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at',    sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('deleted_at',    sa.DateTime(timezone=True), nullable=True),
        )
        print("  ✅ Created device_tokens (incl. is_active)")
    else:
        print("  ℹ️  device_tokens already exists")

    # =========================================================================
    # [D] notification_preferences + device_tokens.is_active backfill (003/006)
    # =========================================================================
    print("\n--- [D] Notification Preferences ---")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'notification_preferences' not in existing_tables:
        op.create_table(
            'notification_preferences',
            sa.Column('id',                     sa.String(36), primary_key=True),
            sa.Column('user_id',                sa.String(36),
                      sa.ForeignKey('users.id', ondelete='CASCADE'),
                      nullable=False, unique=True),
            sa.Column('votes_enabled',          sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('alerts_enabled',         sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('tasks_enabled',          sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('constitutional_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('quiet_hours_start',      sa.String(5), nullable=True),
            sa.Column('quiet_hours_end',        sa.String(5), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'])
        print("  ✅ Created notification_preferences")
    else:
        print("  ℹ️  notification_preferences already exists")

    # Backfill device_tokens.is_active for pre-existing tables that lack it
    if 'device_tokens' in existing_tables:
        dt_cols = _col_names(inspector, 'device_tokens')
        if 'is_active' not in dt_cols:
            op.add_column('device_tokens',
                          sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
            print("  ✅ Added device_tokens.is_active (backfill)")
        else:
            print("  ℹ️  device_tokens.is_active already exists")

    # =========================================================================
    # [E] audit_logs.screenshot_url + critique_reviews.learning_extracted (003/007)
    # =========================================================================
    print("\n--- [E] Audit Screenshot URL ---")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    audit_cols = _col_names(inspector, 'audit_logs')
    if 'screenshot_url' not in audit_cols:
        op.add_column('audit_logs', sa.Column('screenshot_url', sa.String(500), nullable=True))
        print("  ✅ Added audit_logs.screenshot_url")
    else:
        print("  ℹ️  audit_logs.screenshot_url already exists")

    if 'critique_reviews' in existing_tables:
        critique_cols = _col_names(inspector, 'critique_reviews')
        if 'learning_extracted' not in critique_cols:
            op.add_column('critique_reviews',
                          sa.Column('learning_extracted', sa.Boolean(),
                                    nullable=False, server_default='false'))
            print("  ✅ Added critique_reviews.learning_extracted")
        else:
            print("  ℹ️  critique_reviews.learning_extracted already exists")
    else:
        print("  ⚠️  critique_reviews not found — skipping")

    # =========================================================================
    # [F] Federation HMAC back-fill (003/008) — idempotent; signing_key is
    #     already in the CREATE TABLE above for fresh installs
    # =========================================================================
    print("\n--- [F] Federation HMAC back-fill ---")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'federated_instances' in existing_tables:
        fi_cols = _col_names(inspector, 'federated_instances')
        if 'signing_key' not in fi_cols:
            op.add_column('federated_instances',
                          sa.Column('signing_key', sa.String(255), nullable=True))
            op.execute(
                "UPDATE federated_instances "
                "SET signing_key = shared_secret_hash WHERE signing_key IS NULL"
            )
            print("  ✅ Added federated_instances.signing_key and back-filled")
        else:
            print("  ℹ️  federated_instances.signing_key already exists")
    else:
        print("  ℹ️  federated_instances not present — skipping HMAC back-fill")

    # =========================================================================
    # [G] A/B Testing — experiments, runs, results, performance cache (003/009)
    # =========================================================================
    print("\n--- [G] A/B Testing ---")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'experiments' not in existing_tables:
        op.create_table(
            'experiments',
            sa.Column('id',              sa.String(36),  primary_key=True),
            sa.Column('name',            sa.String(200), nullable=False),
            sa.Column('description',     sa.Text(),      nullable=True),
            sa.Column('task_template',   sa.Text(),      nullable=False),
            sa.Column('system_prompt',   sa.Text(),      nullable=True),
            sa.Column('test_iterations', sa.Integer(),   nullable=False, server_default='1'),
            sa.Column('created_by',      sa.String(100), nullable=False, server_default='unknown'),
            sa.Column('status',          sa.String(20),  nullable=False, server_default='draft'),
            sa.Column('created_at',      sa.DateTime(),  nullable=False, server_default=sa.func.now()),
            sa.Column('started_at',      sa.DateTime(),  nullable=True),
            sa.Column('completed_at',    sa.DateTime(),  nullable=True),
        )
        print("  ✅ Created experiments")
    else:
        print("  ℹ️  experiments already exists — applying schema hardening")
        exp_cols = _col_names(inspector, 'experiments')
        if 'created_by' in exp_cols:
            conn.execute(sa.text(
                "UPDATE experiments SET created_by = 'unknown' WHERE created_by IS NULL"
            ))
            op.alter_column('experiments', 'created_by', nullable=False, server_default='unknown')
            print("  ✅ Hardened experiments.created_by (NOT NULL)")
        else:
            op.add_column('experiments',
                          sa.Column('created_by', sa.String(100), nullable=False, server_default='unknown'))
            print("  ✅ Added experiments.created_by")

    inspector = Inspector.from_engine(conn)
    for idx_name, columns in [
        ('ix_experiments_status',            ['status']),
        ('ix_experiments_created_at',        ['created_at']),
        ('ix_experiments_created_by_status', ['created_by', 'status']),
    ]:
        if not _index_exists(inspector, 'experiments', idx_name):
            op.create_index(idx_name, 'experiments', columns)
            print(f"  ✅ Created index {idx_name}")
        else:
            print(f"  ℹ️  {idx_name} already exists")

    if 'experiment_runs' not in existing_tables:
        op.create_table(
            'experiment_runs',
            sa.Column('id',                        sa.String(36),  primary_key=True),
            sa.Column('experiment_id',             sa.String(36),
                      sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
            sa.Column('config_id',                 sa.String(36),  nullable=True),
            sa.Column('model_name',                sa.String(100), nullable=True),
            sa.Column('iteration_number',          sa.Integer(),   nullable=False, server_default='1'),
            sa.Column('status',                    sa.String(20),  nullable=False, server_default='pending'),
            sa.Column('started_at',                sa.DateTime(),  nullable=True),
            sa.Column('completed_at',              sa.DateTime(),  nullable=True),
            sa.Column('error_message',             sa.Text(),      nullable=True),
            sa.Column('output_text',               sa.Text(),      nullable=True),
            sa.Column('tokens_used',               sa.Integer(),   nullable=True),
            sa.Column('latency_ms',                sa.Integer(),   nullable=True),
            sa.Column('cost_usd',                  sa.Float(),     nullable=True),
            sa.Column('critic_plan_score',         sa.Float(),     nullable=True),
            sa.Column('critic_code_score',         sa.Float(),     nullable=True),
            sa.Column('critic_output_score',       sa.Float(),     nullable=True),
            sa.Column('overall_quality_score',     sa.Float(),     nullable=True),
            sa.Column('critic_feedback',           sa.JSON(),      nullable=True),
            sa.Column('constitutional_violations', sa.Integer(),   nullable=False, server_default='0'),
        )
        print("  ✅ Created experiment_runs")
    else:
        print("  ℹ️  experiment_runs already exists")

    inspector = Inspector.from_engine(conn)
    for idx_name, columns in [
        ('ix_runs_experiment_id',     ['experiment_id']),
        ('ix_runs_experiment_status', ['experiment_id', 'status']),
    ]:
        if not _index_exists(inspector, 'experiment_runs', idx_name):
            op.create_index(idx_name, 'experiment_runs', columns)
            print(f"  ✅ Created index {idx_name}")
        else:
            print(f"  ℹ️  {idx_name} already exists")

    if 'experiment_results' not in existing_tables:
        op.create_table(
            'experiment_results',
            sa.Column('id',                       sa.String(36),  primary_key=True),
            sa.Column('experiment_id',            sa.String(36),
                      sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
            sa.Column('winner_config_id',         sa.String(36),  nullable=True),
            sa.Column('winner_model_name',        sa.String(100), nullable=True),
            sa.Column('selection_reason',         sa.Text(),      nullable=True),
            sa.Column('model_comparisons',        sa.JSON(),      nullable=True),
            sa.Column('statistical_significance', sa.Float(),     nullable=True),
            sa.Column('recommended_for_similar',  sa.Boolean(),   nullable=False, server_default='false'),
            sa.Column('confidence_score',         sa.Float(),     nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        print("  ✅ Created experiment_results")
    else:
        print("  ℹ️  experiment_results already exists")

    inspector = Inspector.from_engine(conn)
    if not _index_exists(inspector, 'experiment_results', 'ix_results_experiment_id'):
        op.create_index('ix_results_experiment_id', 'experiment_results', ['experiment_id'])
        print("  ✅ Created index ix_results_experiment_id")
    else:
        print("  ℹ️  ix_results_experiment_id already exists")

    if 'model_performance_cache' not in existing_tables:
        op.create_table(
            'model_performance_cache',
            sa.Column('id',                         sa.String(36),  primary_key=True),
            sa.Column('task_category',              sa.String(50),  nullable=False),
            sa.Column('task_complexity',            sa.String(20),  nullable=True),
            sa.Column('best_config_id',             sa.String(36),  nullable=True),
            sa.Column('best_model_name',            sa.String(100), nullable=True),
            sa.Column('avg_latency_ms',             sa.Integer(),   nullable=True),
            sa.Column('avg_cost_usd',               sa.Float(),     nullable=True),
            sa.Column('avg_quality_score',          sa.Float(),     nullable=True),
            sa.Column('success_rate',               sa.Float(),     nullable=True),
            sa.Column('sample_size',                sa.Integer(),   nullable=False, server_default='0'),
            sa.Column('derived_from_experiment_id', sa.String(36),  nullable=True),
            sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        print("  ✅ Created model_performance_cache")
    else:
        print("  ℹ️  model_performance_cache already exists — applying schema hardening")
        mpc_cols = _col_names(inspector, 'model_performance_cache')
        if 'last_updated' in mpc_cols:
            conn.execute(sa.text(
                "UPDATE model_performance_cache SET last_updated = NOW() WHERE last_updated IS NULL"
            ))
            op.alter_column('model_performance_cache', 'last_updated',
                            nullable=False, server_default=sa.func.now())
            print("  ✅ Hardened model_performance_cache.last_updated (NOT NULL)")

    inspector = Inspector.from_engine(conn)
    if not _constraint_exists(inspector, 'model_performance_cache', 'uq_perf_cache_task_category'):
        conn.execute(sa.text("""
            DELETE FROM model_performance_cache
            WHERE id NOT IN (
                SELECT DISTINCT ON (task_category) id
                FROM model_performance_cache
                ORDER BY task_category, last_updated DESC NULLS LAST
            )
        """))
        op.create_unique_constraint(
            'uq_perf_cache_task_category', 'model_performance_cache', ['task_category'],
        )
        print("  ✅ Created unique constraint uq_perf_cache_task_category")
    else:
        print("  ℹ️  uq_perf_cache_task_category already exists")

    inspector = Inspector.from_engine(conn)
    if not _index_exists(inspector, 'model_performance_cache', 'ix_perf_cache_last_updated'):
        op.create_index('ix_perf_cache_last_updated', 'model_performance_cache', ['last_updated'])
        print("  ✅ Created index ix_perf_cache_last_updated")
    else:
        print("  ℹ️  ix_perf_cache_last_updated already exists")

    # =========================================================================
    # [H] Outbound Webhooks (004_webhooks)
    # =========================================================================
    print("\n--- [H] Outbound Webhooks ---")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'webhook_subscriptions' not in existing_tables:
        op.create_table(
            'webhook_subscriptions',
            sa.Column('id',          sa.String(36),  primary_key=True),
            sa.Column('user_id',     sa.String(36),
                      sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('url',         sa.String(500), nullable=False),
            sa.Column('secret',      sa.String(255), nullable=False),
            sa.Column('description', sa.String(500), nullable=True),
            sa.Column('events',      sa.JSON(),      nullable=False),
            sa.Column('is_active',   sa.Boolean(),   nullable=False, server_default='true'),
            sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_webhook_subscriptions_user_id',   'webhook_subscriptions', ['user_id'])
        op.create_index('ix_webhook_subscriptions_is_active', 'webhook_subscriptions', ['is_active'])
        print("  ✅ Created webhook_subscriptions")
    else:
        print("  ℹ️  webhook_subscriptions already exists")

    if 'webhook_delivery_logs' not in existing_tables:
        op.create_table(
            'webhook_delivery_logs',
            sa.Column('id',               sa.String(36), primary_key=True),
            sa.Column('subscription_id',  sa.String(36),
                      sa.ForeignKey('webhook_subscriptions.id', ondelete='CASCADE'), nullable=False),
            sa.Column('delivery_id',      sa.String(36), nullable=False, unique=True),
            sa.Column('event_type',       sa.String(50), nullable=False),
            sa.Column('payload',          sa.JSON(),     nullable=False),
            sa.Column('status_code',      sa.Integer(),  nullable=True),
            sa.Column('response_body',    sa.Text(),     nullable=True),
            sa.Column('attempts',         sa.Integer(),  nullable=False, server_default='0'),
            sa.Column('max_attempts',     sa.Integer(),  nullable=False, server_default='5'),
            sa.Column('delivered_at',     sa.DateTime(timezone=True), nullable=True),
            sa.Column('next_retry_at',    sa.DateTime(timezone=True), nullable=True),
            sa.Column('failed_at',        sa.DateTime(timezone=True), nullable=True),
            sa.Column('error',            sa.Text(),     nullable=True),
            sa.Column('created_at',       sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_webhook_delivery_logs_subscription_id', 'webhook_delivery_logs', ['subscription_id'])
        op.create_index('ix_webhook_delivery_logs_event_type',      'webhook_delivery_logs', ['event_type'])
        op.create_index('ix_webhook_delivery_logs_next_retry',      'webhook_delivery_logs', ['next_retry_at'])
        print("  ✅ Created webhook_delivery_logs")
    else:
        print("  ℹ️  webhook_delivery_logs already exists")

    # =========================================================================
    # [I] Composite index on user_model_configs (005_models)
    # =========================================================================
    print("\n--- [I] user_model_configs index ---")

    inspector = Inspector.from_engine(conn)
    if not _index_exists(inspector, 'user_model_configs', 'ix_user_model_configs_user_default'):
        op.create_index(
            'ix_user_model_configs_user_default',
            'user_model_configs',
            ['user_id', 'is_default'],
            unique=False,
        )
        print("  ✅ Created ix_user_model_configs_user_default")
    else:
        print("  ℹ️  ix_user_model_configs_user_default already exists")

    # =========================================================================
    # [J] Workflow — workflow_executions + workflow_subtasks + tasks columns
    #     Uses the FINAL correct schema (006 + 011 merged):
    #       • workflow_executions: no UNIQUE on workflow_id, FK → workflows.id,
    #         correct column set (incl. current_step_index, started_at, triggered_by)
    #       • workflow_subtasks: FK → workflows.id, BaseEntity columns
    # =========================================================================
    print("\n--- [J] Workflow Executions & Subtasks ---")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    # workflows MUST exist before workflow_executions/workflow_subtasks reference it via FK.
    # Columns match the Workflow SQLAlchemy model in backend/models/entities/workflow.py.
    if 'workflows' not in existing_tables:
        op.create_table(
            'workflows',
            # BaseEntity columns
            sa.Column('id',          sa.String(36),  primary_key=True),
            sa.Column('agentium_id', sa.String(20),  unique=True, nullable=False),
            sa.Column('is_active',   sa.Boolean(),   nullable=False, server_default='true'),
            sa.Column('created_at',  sa.DateTime(),  nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at',  sa.DateTime(),  nullable=False, server_default=sa.text('NOW()')),
            sa.Column('deleted_at',  sa.DateTime(),  nullable=True),
            # Workflow-specific columns
            sa.Column('name',                 sa.String(100), nullable=False),
            sa.Column('description',          sa.Text(),      nullable=True),
            sa.Column('template_json',        sa.JSON(),      nullable=False, server_default='{}'),
            sa.Column('version',              sa.Integer(),   nullable=False, server_default='1'),
            sa.Column('created_by_agent_id',  sa.String(36),
                      sa.ForeignKey('agents.id'), nullable=True),
            sa.Column('schedule_cron',        sa.String(100), nullable=True),
        )
        op.create_index('ix_workflows_created_by_agent_id', 'workflows', ['created_by_agent_id'])
        print("  ✅ Created workflows")
    else:
        print("  ℹ️  workflows already exists")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'workflow_executions' not in existing_tables:
        op.create_table(
            'workflow_executions',
            # BaseEntity
            sa.Column('id',         sa.String(36), primary_key=True),
            sa.Column('is_active',  sa.Boolean(),  nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            # WorkflowExecution columns (final schema from 011)
            sa.Column('workflow_id',         sa.String(36),  nullable=False,
                      ),  # FK added after to allow workflows table to pre-exist check
            sa.Column('original_message',    sa.Text(),      nullable=False),
            sa.Column('status',              sa.String(32),  nullable=False, server_default='pending'),
            sa.Column('context_data',        sa.JSON(),      nullable=False, server_default='{}'),
            sa.Column('error',               sa.Text(),      nullable=True),
            sa.Column('created_by',          sa.String(128), nullable=True),
            sa.Column('completed_at',        sa.DateTime(),  nullable=True),
            # Columns from 011_fix_workflow (added upfront here)
            sa.Column('current_step_index',  sa.Integer(),   nullable=False, server_default='0'),
            sa.Column('started_at',          sa.DateTime(),  nullable=True),
            sa.Column('triggered_by',        sa.String(100), nullable=True),
        )
        op.create_index('ix_workflow_executions_status', 'workflow_executions', ['status'])
        # Add FK to workflows.id (non-unique index)
        op.execute(
            "ALTER TABLE workflow_executions "
            "ADD CONSTRAINT fk_workflow_executions_workflow_id "
            "FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE"
        )
        op.create_index('ix_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'])
        print("  ✅ Created workflow_executions (final schema)")
    else:
        # Table exists from a previous run — apply 011_fix_workflow corrections
        print("  ℹ️  workflow_executions already exists — applying schema corrections")
        we_cols = _col_names(inspector, 'workflow_executions')

        for col_name, col_def in [
            ('current_step_index', sa.Column('current_step_index', sa.Integer(), nullable=False, server_default='0')),
            ('started_at',         sa.Column('started_at',         sa.DateTime(), nullable=True)),
            ('triggered_by',       sa.Column('triggered_by',       sa.String(100), nullable=True)),
        ]:
            if col_name not in we_cols:
                op.add_column('workflow_executions', col_def)
                print(f"  ✅ Added {col_name}")
            else:
                print(f"  ℹ️  {col_name} already exists")

        # Drop any UNIQUE constraint/index on workflow_id
        uc_names = {uc.get('name') for uc in inspector.get_unique_constraints('workflow_executions')}
        idx_names = {idx['name'] for idx in inspector.get_indexes('workflow_executions')}
        dropped_unique = False
        for uc_name in uc_names:
            if uc_name and 'workflow_id' in uc_name.lower():
                op.drop_constraint(uc_name, 'workflow_executions', type_='unique')
                print(f"  ✅ Dropped unique constraint: {uc_name}")
                dropped_unique = True
                break
        if not dropped_unique:
            for idx_name in idx_names:
                if 'workflow_id' in idx_name.lower():
                    idx_info = [i for i in inspector.get_indexes('workflow_executions') if i['name'] == idx_name]
                    if idx_info and idx_info[0].get('unique'):
                        op.drop_index(idx_name, table_name='workflow_executions')
                        print(f"  ✅ Dropped unique index: {idx_name}")
                        break

        # Add FK to workflows.id if missing
        existing_fk_names = _fk_names(inspector, 'workflow_executions')
        if 'fk_workflow_executions_workflow_id' not in existing_fk_names:
            op.execute(
                "ALTER TABLE workflow_executions "
                "ALTER COLUMN workflow_id TYPE VARCHAR(36)"
            )
            op.execute(
                "ALTER TABLE workflow_executions "
                "ADD CONSTRAINT fk_workflow_executions_workflow_id "
                "FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE"
            )
            print("  ✅ workflow_id narrowed to VARCHAR(36) and FK added → workflows.id")
        else:
            print("  ℹ️  FK on workflow_id already exists")

    if 'workflow_subtasks' not in existing_tables:
        op.create_table(
            'workflow_subtasks',
            # BaseEntity
            sa.Column('id',         sa.String(36), primary_key=True),
            sa.Column('is_active',  sa.Boolean(),  nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            # WorkflowSubTask columns (final schema from 011)
            sa.Column('workflow_id',
                      sa.String(36),
                      sa.ForeignKey('workflows.id', ondelete='CASCADE'),
                      nullable=False),
            sa.Column('step_index',           sa.Integer(),   nullable=False, server_default='0'),
            sa.Column('intent',               sa.String(128), nullable=False),
            sa.Column('params',               sa.JSON(),      nullable=False, server_default='{}'),
            sa.Column('depends_on',           sa.JSON(),      nullable=False, server_default='[]'),
            sa.Column('status',               sa.String(32),  nullable=False, server_default='pending'),
            sa.Column('result',               sa.JSON(),      nullable=True),
            sa.Column('error',                sa.Text(),      nullable=True),
            sa.Column('celery_task_id',       sa.String(256), nullable=True),
            sa.Column('schedule_offset_days', sa.Integer(),   nullable=False, server_default='0'),
            sa.Column('scheduled_for',        sa.DateTime(),  nullable=True),
            sa.Column('completed_at',         sa.DateTime(),  nullable=True),
        )
        op.create_index('ix_workflow_subtasks_workflow_id', 'workflow_subtasks', ['workflow_id'])
        op.create_index('ix_workflow_subtasks_status',      'workflow_subtasks', ['status'])
        print("  ✅ Created workflow_subtasks (final schema)")
    else:
        print("  ℹ️  workflow_subtasks already exists")

    # New columns on tasks (006_workflow) — ADD COLUMN IF NOT EXISTS is idempotent
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS workflow_id    VARCHAR(64)  NULL")
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS context_data   JSON         NULL")
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS celery_task_id VARCHAR(256) NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_workflow_id ON tasks (workflow_id)")
    print("  ✅ Ensured tasks.workflow_id, context_data, celery_task_id columns + index")

    # =========================================================================
    # [K] Settings improvements (007_improvements)
    # =========================================================================
    print("\n--- [K] Settings Improvements ---")

    inspector = Inspector.from_engine(conn)

    audit_cols = _col_names(inspector, 'audit_logs')
    if 'actor_id' in audit_cols:
        op.alter_column(
            'audit_logs', 'actor_id',
            existing_type=sa.String(10),
            type_=sa.String(100),
            nullable=False,
        )
        print("  ✅ audit_logs.actor_id widened to VARCHAR(100)")
    else:
        print("  ⚠️  actor_id not found on audit_logs — skipping widen")

    user_cols = _col_names(inspector, 'users')
    if 'last_login_at' not in user_cols:
        op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
        print("  ✅ Added users.last_login_at")
    else:
        print("  ℹ️  users.last_login_at already exists")

    # =========================================================================
    # [L] Skills page (008_skills)
    #     skills table is already created by 002_migration — ensure description
    #     column is present and create skill_submissions if missing.
    # =========================================================================
    print("\n--- [L] Skills page ---")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'skills' not in existing_tables:
        # Fresh environment — create the full table
        op.create_table(
            'skills',
            sa.Column('id',          sa.String(36),  primary_key=True),
            sa.Column('is_active',   sa.Boolean(),   nullable=False, server_default='true'),
            sa.Column('created_at',  sa.DateTime(),  nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at',  sa.DateTime(),  nullable=False, server_default=sa.text('NOW()')),
            sa.Column('deleted_at',  sa.DateTime(),  nullable=True),
            sa.Column('skill_id',     sa.String(50),  nullable=False),
            sa.Column('skill_name',   sa.String(100), nullable=False),
            sa.Column('display_name', sa.String(200), nullable=False),
            sa.Column('description',  sa.String(300), nullable=True),
            sa.Column('skill_type',  sa.String(50), nullable=False),
            sa.Column('domain',      sa.String(50), nullable=False),
            sa.Column('tags',        sa.JSON(),     nullable=False, server_default='[]'),
            sa.Column('complexity',  sa.String(20), nullable=False),
            sa.Column('chroma_id',         sa.String(100), nullable=False),
            sa.Column('chroma_collection', sa.String(50),  nullable=False, server_default='agent_skills'),
            sa.Column('embedding_model',   sa.String(100), nullable=False,
                      server_default='sentence-transformers/all-MiniLM-L6-v2'),
            sa.Column('creator_tier',    sa.String(20),  nullable=False),
            sa.Column('creator_id',      sa.String(20),  nullable=False),
            sa.Column('parent_skill_id', sa.String(50),  nullable=True),
            sa.Column('task_origin',     sa.String(50),  nullable=True),
            sa.Column('success_rate',    sa.Float(),   nullable=False, server_default='0.0'),
            sa.Column('usage_count',     sa.Integer(), nullable=False, server_default='0'),
            sa.Column('retrieval_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_retrieved',  sa.DateTime(), nullable=True),
            sa.Column('constitution_compliant', sa.Boolean(),   nullable=False, server_default='false'),
            sa.Column('verification_status',    sa.String(20),  nullable=False, server_default='pending'),
            sa.Column('verified_by',            sa.String(20),  nullable=True),
            sa.Column('verified_at',            sa.DateTime(),  nullable=True),
            sa.Column('rejection_reason',       sa.String(500), nullable=True),
        )
        op.create_index('ix_skills_skill_id',           'skills', ['skill_id'],                                   unique=True)
        op.create_index('ix_skills_verification_usage', 'skills', ['verification_status', 'usage_count'])
        op.create_index('ix_skills_creator_id',         'skills', ['creator_id'])
        op.create_index('ix_skills_domain_usage',       'skills', ['domain', 'verification_status', 'usage_count'])
        print("  ✅ Created skills table")
    else:
        # Table created by 002_migration — ensure description column is present
        skill_cols = _col_names(inspector, 'skills')
        if 'description' not in skill_cols:
            op.add_column('skills', sa.Column('description', sa.String(300), nullable=True))
            print("  ✅ Added skills.description column")
        else:
            print("  ℹ️  skills already has description column")

    if 'skill_submissions' not in existing_tables:
        op.create_table(
            'skill_submissions',
            sa.Column('id',         sa.String(36), primary_key=True),
            sa.Column('is_active',  sa.Boolean(),  nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.Column('submission_id', sa.String(50), nullable=False),
            sa.Column('skill_id',      sa.String(50),
                      sa.ForeignKey('skills.skill_id', ondelete='CASCADE'), nullable=False),
            sa.Column('submitted_by',  sa.String(20),   nullable=False),
            sa.Column('submitted_at',  sa.DateTime(),   nullable=True, server_default=sa.text('NOW()')),
            sa.Column('status',           sa.String(20),   nullable=False, server_default='pending'),
            sa.Column('council_vote_id',  sa.String(50),   nullable=True),
            sa.Column('reviewed_by',      sa.String(20),   nullable=True),
            sa.Column('reviewed_at',      sa.DateTime(),   nullable=True),
            sa.Column('review_notes',     sa.String(1000), nullable=True),
            sa.Column('skill_data',       sa.JSON(),       nullable=False, server_default='{}'),
        )
        op.create_index('ix_skill_submissions_submission_id', 'skill_submissions', ['submission_id'], unique=True)
        op.create_index('ix_skill_submissions_skill_id',      'skill_submissions', ['skill_id'])
        op.create_index('ix_skill_submissions_status',        'skill_submissions', ['status'])
        op.create_index('ix_skill_submissions_submitted_by',  'skill_submissions', ['submitted_by'])
        print("  ✅ Created skill_submissions")
    else:
        print("  ℹ️  skill_submissions already exists")

    # =========================================================================
    # [M] Task Delegation Engine (009_task_delegation)
    # =========================================================================
    print("\n--- [M] Task Delegation Engine ---")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'task_dependencies' not in existing_tables:
        op.create_table(
            'task_dependencies',
            # BaseEntity columns (model inherits BaseEntity — agentium_id etc. are required)
            sa.Column('id',          sa.String(36), primary_key=True),
            sa.Column('agentium_id', sa.String(20), unique=True, nullable=False),
            sa.Column('is_active',   sa.Boolean(),  nullable=False, server_default='true'),
            sa.Column('created_at',  sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('updated_at',  sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('deleted_at',  sa.DateTime(), nullable=True),
            # TaskDependency-specific columns
            sa.Column('parent_task_id',   sa.String(36),
                      sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
            sa.Column('child_task_id',    sa.String(36),
                      sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
            sa.Column('dependency_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('status',           sa.String(20), nullable=False, server_default='pending'),
        )
        op.create_index('ix_task_deps_parent', 'task_dependencies', ['parent_task_id'])
        op.create_index('ix_task_deps_child',  'task_dependencies', ['child_task_id'])
        op.create_index('ix_task_deps_order',  'task_dependencies', ['parent_task_id', 'dependency_order'])
        print("  ✅ Created task_dependencies")
    else:
        print("  ℹ️  task_dependencies already exists")

    task_cols = _col_names(inspector, 'tasks')

    if 'complexity_score' not in task_cols:
        op.add_column('tasks', sa.Column('complexity_score', sa.Integer(), nullable=True))
        print("  ✅ Added tasks.complexity_score")
    else:
        print("  ℹ️  tasks.complexity_score already exists")

    if 'escalation_timeout_seconds' not in task_cols:
        op.add_column('tasks', sa.Column(
            'escalation_timeout_seconds', sa.Integer(), nullable=False, server_default='300',
        ))
        print("  ✅ Added tasks.escalation_timeout_seconds")
    else:
        print("  ℹ️  tasks.escalation_timeout_seconds already exists")

    if 'delegation_metadata' not in task_cols:
        op.add_column('tasks', sa.Column('delegation_metadata', sa.JSON(), nullable=True))
        print("  ✅ Added tasks.delegation_metadata")
    else:
        print("  ℹ️  tasks.delegation_metadata already exists")

    # =========================================================================
    # [N] Self-Healing (010_self_healing) — agents.last_heartbeat_at
    # =========================================================================
    print("\n--- [N] Self-Healing ---")

    inspector = Inspector.from_engine(conn)
    agent_cols = _col_names(inspector, 'agents')

    if 'last_heartbeat_at' not in agent_cols:
        op.add_column('agents', sa.Column('last_heartbeat_at', sa.DateTime(), nullable=True))
        op.create_index('ix_agents_last_heartbeat_at', 'agents', ['last_heartbeat_at'])
        print("  ✅ Added agents.last_heartbeat_at")
    else:
        print("  ℹ️  agents.last_heartbeat_at already exists")

    print("\n" + "=" * 70)
    print("✅ Consolidated migration 003_consolidated completed!")
    print("=" * 70)
    print("  [A] reasoning_traces, reasoning_steps, tasks.latest_trace_id")
    print("  [B] Chat performance indexes")
    print("  [C] Phase 11: RBAC, delegations, federation, plugins, device_tokens")
    print("  [D] notification_preferences, device_tokens.is_active")
    print("  [E] audit_logs.screenshot_url, critique_reviews.learning_extracted")
    print("  [F] federated_instances.signing_key back-fill")
    print("  [G] experiments, experiment_runs, experiment_results, model_performance_cache")
    print("  [H] webhook_subscriptions, webhook_delivery_logs")
    print("  [I] user_model_configs composite index")
    print("  [J] workflow_executions + workflow_subtasks (final schema), tasks workflow cols")
    print("  [K] audit_logs.actor_id widened, users.last_login_at")
    print("  [L] skills.description, skill_submissions")
    print("  [M] task_dependencies, tasks delegation/complexity columns")
    print("  [N] agents.last_heartbeat_at")
    print("=" * 70)


# ── downgrade ─────────────────────────────────────────────────────────────────

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    print("🔄 Downgrading 003_consolidated ...")

    # ── [N] Self-Healing ──────────────────────────────────────────────────────
    agent_cols = _col_names(inspector, 'agents')
    if 'last_heartbeat_at' in agent_cols:
        op.drop_index('ix_agents_last_heartbeat_at', table_name='agents')
        op.drop_column('agents', 'last_heartbeat_at')
        print("  ✅ Dropped agents.last_heartbeat_at")

    # ── [M] Task Delegation ───────────────────────────────────────────────────
    task_cols = _col_names(inspector, 'tasks')
    for col in ('delegation_metadata', 'escalation_timeout_seconds', 'complexity_score'):
        if col in task_cols:
            op.drop_column('tasks', col)
            print(f"  ✅ Dropped tasks.{col}")

    if 'task_dependencies' in existing_tables:
        op.drop_index('ix_task_deps_order',  table_name='task_dependencies')
        op.drop_index('ix_task_deps_child',  table_name='task_dependencies')
        op.drop_index('ix_task_deps_parent', table_name='task_dependencies')
        op.drop_table('task_dependencies')
        print("  ✅ Dropped task_dependencies")

    # ── [L] Skills page ───────────────────────────────────────────────────────
    if 'skill_submissions' in existing_tables:
        op.drop_index('ix_skill_submissions_submitted_by',  table_name='skill_submissions')
        op.drop_index('ix_skill_submissions_status',        table_name='skill_submissions')
        op.drop_index('ix_skill_submissions_skill_id',      table_name='skill_submissions')
        op.drop_index('ix_skill_submissions_submission_id', table_name='skill_submissions')
        op.drop_table('skill_submissions')
        print("  ✅ Dropped skill_submissions")

    if 'skills' in existing_tables:
        for idx in ('ix_skills_domain_usage', 'ix_skills_creator_id',
                    'ix_skills_verification_usage', 'ix_skills_skill_id'):
            try:
                op.drop_index(idx, table_name='skills')
            except Exception:
                pass
        op.drop_table('skills')
        print("  ✅ Dropped skills")

    # ── [K] Settings improvements ─────────────────────────────────────────────
    inspector = Inspector.from_engine(conn)
    user_cols = _col_names(inspector, 'users')
    if 'last_login_at' in user_cols:
        op.drop_column('users', 'last_login_at')
        print("  ✅ Dropped users.last_login_at")

    audit_cols = _col_names(inspector, 'audit_logs')
    if 'actor_id' in audit_cols:
        op.alter_column('audit_logs', 'actor_id',
                        existing_type=sa.String(100), type_=sa.String(10), nullable=False)
        print("  ✅ Restored audit_logs.actor_id to VARCHAR(10)")

    # ── [J] Workflow ──────────────────────────────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_tasks_workflow_id")
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS celery_task_id")
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS context_data")
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS workflow_id")
    print("  ✅ Dropped tasks workflow columns")

    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'workflow_subtasks' in existing_tables:
        op.drop_index('ix_workflow_subtasks_status',      table_name='workflow_subtasks')
        op.drop_index('ix_workflow_subtasks_workflow_id', table_name='workflow_subtasks')
        op.drop_table('workflow_subtasks')
        print("  ✅ Dropped workflow_subtasks")

    if 'workflow_executions' in existing_tables:
        fks = inspector.get_foreign_keys('workflow_executions')
        for fk in fks:
            if fk.get('name') == 'fk_workflow_executions_workflow_id':
                op.drop_constraint('fk_workflow_executions_workflow_id',
                                   'workflow_executions', type_='foreignkey')
                print("  ✅ Dropped FK fk_workflow_executions_workflow_id")
        op.drop_index('ix_workflow_executions_status',     table_name='workflow_executions')
        op.drop_index('ix_workflow_executions_workflow_id', table_name='workflow_executions')
        op.drop_table('workflow_executions')
        print("  ✅ Dropped workflow_executions")

    # Drop workflows AFTER dependents (workflow_executions, workflow_subtasks)
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())
    if 'workflows' in existing_tables:
        try:
            op.drop_index('ix_workflows_created_by_agent_id', table_name='workflows')
        except Exception:
            pass
        op.drop_table('workflows')
        print("  ✅ Dropped workflows")

    # ── [I] user_model_configs index ──────────────────────────────────────────
    inspector = Inspector.from_engine(conn)
    if _index_exists(inspector, 'user_model_configs', 'ix_user_model_configs_user_default'):
        op.drop_index('ix_user_model_configs_user_default', table_name='user_model_configs')
        print("  ✅ Dropped ix_user_model_configs_user_default")

    # ── [H] Webhooks ──────────────────────────────────────────────────────────
    existing_tables = set(inspector.get_table_names())
    if 'webhook_delivery_logs' in existing_tables:
        op.drop_table('webhook_delivery_logs')
        print("  ✅ Dropped webhook_delivery_logs")
    if 'webhook_subscriptions' in existing_tables:
        op.drop_table('webhook_subscriptions')
        print("  ✅ Dropped webhook_subscriptions")

    # ── [G] A/B Testing ───────────────────────────────────────────────────────
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'model_performance_cache' in existing_tables:
        try:
            op.drop_index('ix_perf_cache_last_updated', table_name='model_performance_cache')
        except Exception:
            pass
        try:
            op.drop_constraint('uq_perf_cache_task_category', 'model_performance_cache', type_='unique')
        except Exception:
            pass
        op.drop_table('model_performance_cache')
        print("  ✅ Dropped model_performance_cache")

    for table, indexes in [
        ('experiment_results', ['ix_results_experiment_id']),
        ('experiment_runs',    ['ix_runs_experiment_status', 'ix_runs_experiment_id']),
        ('experiments',        ['ix_experiments_created_by_status', 'ix_experiments_created_at', 'ix_experiments_status']),
    ]:
        if table in existing_tables:
            for idx in indexes:
                try:
                    op.drop_index(idx, table_name=table)
                except Exception:
                    pass
            op.drop_table(table)
            print(f"  ✅ Dropped {table}")

    # ── [F/C] Federation HMAC / Phase 11 ──────────────────────────────────────
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'federated_instances' in existing_tables:
        fi_cols = _col_names(inspector, 'federated_instances')
        if 'signing_key' in fi_cols:
            op.drop_column('federated_instances', 'signing_key')
            print("  ✅ Dropped federated_instances.signing_key")

    # ── [E] Audit columns ─────────────────────────────────────────────────────
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    if 'critique_reviews' in existing_tables:
        if 'learning_extracted' in _col_names(inspector, 'critique_reviews'):
            op.drop_column('critique_reviews', 'learning_extracted')
            print("  ✅ Dropped critique_reviews.learning_extracted")

    audit_cols = _col_names(inspector, 'audit_logs')
    if 'screenshot_url' in audit_cols:
        op.drop_column('audit_logs', 'screenshot_url')
        print("  ✅ Dropped audit_logs.screenshot_url")

    # ── [D] Notification preferences ─────────────────────────────────────────
    if 'notification_preferences' in existing_tables:
        op.drop_table('notification_preferences')
        print("  ✅ Dropped notification_preferences")

    # ── [C] Phase 11 Ecosystem ────────────────────────────────────────────────
    for tbl in ('device_tokens', 'plugin_reviews', 'plugin_installations', 'plugins',
                'federated_votes', 'federated_tasks', 'federated_instances', 'delegations'):
        if tbl in existing_tables:
            op.drop_table(tbl)
            print(f"  ✅ Dropped {tbl}")

    inspector = Inspector.from_engine(conn)
    user_cols = _col_names(inspector, 'users')
    if 'role_expires_at' in user_cols:
        op.drop_column('users', 'role_expires_at')
    if 'delegated_by_id' in user_cols:
        try:
            op.drop_constraint('fk_users_delegated_by_id', 'users', type_='foreignkey')
        except Exception:
            pass
        op.drop_column('users', 'delegated_by_id')
    if 'role' in user_cols:
        op.drop_column('users', 'role')
    print("  ✅ Reverted users RBAC columns")

    # ── [B] Chat indexes ──────────────────────────────────────────────────────
    inspector = Inspector.from_engine(conn)
    for idx, tbl in [
        ('idx_conversations_user_active',   'conversations'),
        ('idx_conversations_user_last_msg', 'conversations'),
        ('idx_chat_messages_conversation',  'chat_messages'),
        ('idx_chat_messages_user_created',  'chat_messages'),
    ]:
        if _index_exists(inspector, tbl, idx):
            op.drop_index(idx, table_name=tbl)
            print(f"  ✅ Dropped {idx}")

    # ── [A] Reasoning Traces ──────────────────────────────────────────────────
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())
    task_cols = _col_names(inspector, 'tasks')

    if 'latest_trace_id' in task_cols:
        op.drop_column('tasks', 'latest_trace_id')
        print("  ✅ Dropped tasks.latest_trace_id")

    # Restore db_maintenance_config ANALYZE list
    try:
        row = conn.execute(text(
            "SELECT config_value FROM db_maintenance_config WHERE config_key = 'analyze_tables'"
        )).fetchone()
        if row:
            current = json.loads(row[0])
            restored = [t for t in current if t not in ('reasoning_traces', 'reasoning_steps')]
            conn.execute(text(
                "UPDATE db_maintenance_config SET config_value = :val, updated_at = NOW() "
                "WHERE config_key = 'analyze_tables'"
            ), {"val": json.dumps(restored)})
            print("  ✅ Restored db_maintenance_config ANALYZE list")
    except Exception as exc:
        print(f"  ℹ️  Could not restore db_maintenance_config: {exc}")

    if 'reasoning_steps' in existing_tables:
        for idx in ('ix_reasoning_steps_trace_id_sequence', 'ix_reasoning_steps_outcome',
                    'ix_reasoning_steps_phase', 'ix_reasoning_steps_trace_id',
                    'ix_reasoning_steps_step_id'):
            try:
                op.drop_index(idx, table_name='reasoning_steps')
            except Exception:
                pass
        op.drop_table('reasoning_steps')
        print("  ✅ Dropped reasoning_steps")

    if 'reasoning_traces' in existing_tables:
        for idx in ('ix_reasoning_traces_validation', 'ix_reasoning_traces_created_at',
                    'ix_reasoning_traces_phase', 'ix_reasoning_traces_outcome',
                    'ix_reasoning_traces_agent_id', 'ix_reasoning_traces_task_id',
                    'ix_reasoning_traces_trace_id'):
            try:
                op.drop_index(idx, table_name='reasoning_traces')
            except Exception:
                pass
        op.drop_table('reasoning_traces')
        print("  ✅ Dropped reasoning_traces")

    print("\n✅ Downgrade 003_consolidated completed.")