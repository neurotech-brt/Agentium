"""
Ecosystem Expansion (Phase 11)
Adds Multi-User RBAC, Federation, Plugin Marketplace, and Mobile API tables.

Revision ID: 005_phase11_ecosystem
Revises: 004_chat_indexes
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '005_phase11_ecosystem'
down_revision = '004_chat_indexes'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    print("🚀 Starting migration 005_phase11_ecosystem...")

    # =========================================================================
    # 1. Update `users` table for RBAC (Phase 11.1)
    # =========================================================================
    user_columns = {col['name'] for col in inspector.get_columns('users')}
    
    if 'role' not in user_columns:
        op.add_column('users', sa.Column('role', sa.String(30), nullable=False, server_default='observer'))
        print("  ✅ Added users.role")

    if 'delegated_by_id' not in user_columns:
        op.add_column('users', sa.Column('delegated_by_id', sa.String(36), nullable=True))
        op.create_foreign_key('fk_users_delegated_by_id', 'users', 'users', ['delegated_by_id'], ['id'])
        print("  ✅ Added users.delegated_by_id")

    if 'role_expires_at' not in user_columns:
        op.add_column('users', sa.Column('role_expires_at', sa.DateTime(timezone=True), nullable=True))
        print("  ✅ Added users.role_expires_at")

    # =========================================================================
    # 2. `delegations` table (Phase 11.1)
    # =========================================================================
    if 'delegations' not in existing_tables:
        op.create_table(
            'delegations',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('grantor_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('grantee_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('capabilities', sa.JSON(), nullable=False),
            sa.Column('reason', sa.String(500), nullable=True),
            sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_emergency', sa.Boolean(), nullable=False, server_default='false'),
            
            # BaseEntity
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        op.create_index('ix_delegations_grantor_id', 'delegations', ['grantor_id'])
        op.create_index('ix_delegations_grantee_id', 'delegations', ['grantee_id'])
        print("  ✅ Created delegations table")

    # =========================================================================
    # 3. Federation tables (Phase 11.2)
    # =========================================================================
    if 'federated_instances' not in existing_tables:
        op.create_table(
            'federated_instances',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('base_url', sa.String(255), nullable=False, unique=True),
            sa.Column('shared_secret_hash', sa.String(255), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('trust_level', sa.String(20), nullable=False, server_default='limited'),
            sa.Column('capabilities_shared', sa.JSON(), nullable=True),
            sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True),
            
            # BaseEntity
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        print("  ✅ Created federated_instances table")

    if 'federated_tasks' not in existing_tables:
        op.create_table(
            'federated_tasks',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('source_instance_id', sa.String(36), sa.ForeignKey('federated_instances.id'), nullable=True),
            sa.Column('target_instance_id', sa.String(36), sa.ForeignKey('federated_instances.id'), nullable=True),
            sa.Column('original_task_id', sa.String(36), nullable=False),
            sa.Column('local_task_id', sa.String(36), sa.ForeignKey('tasks.id'), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('delegated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            
            # BaseEntity
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        print("  ✅ Created federated_tasks table")

    if 'federated_votes' not in existing_tables:
        op.create_table(
            'federated_votes',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('proposal_id', sa.String(36), nullable=False),
            sa.Column('participating_instances', sa.JSON(), nullable=True),
            sa.Column('votes', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='open'),
            sa.Column('closes_at', sa.DateTime(timezone=True), nullable=False),
            
            # BaseEntity
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        print("  ✅ Created federated_votes table")

    # =========================================================================
    # 4. Plugin Marketplace tables (Phase 11.3)
    # =========================================================================
    if 'plugins' not in existing_tables:
        op.create_table(
            'plugins',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False, unique=True),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('author', sa.String(100), nullable=False),
            sa.Column('version', sa.String(20), nullable=False),
            sa.Column('plugin_type', sa.String(50), nullable=False),
            sa.Column('source_url', sa.String(255), nullable=True),
            sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('install_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('rating', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('revenue_share_percent', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('config_schema', sa.JSON(), nullable=True),
            sa.Column('entry_point', sa.String(255), nullable=False),
            sa.Column('dependencies', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
            sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
            
            # BaseEntity
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        print("  ✅ Created plugins table")

    if 'plugin_installations' not in existing_tables:
        op.create_table(
            'plugin_installations',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('plugin_id', sa.String(36), sa.ForeignKey('plugins.id', ondelete='CASCADE'), nullable=False),
            sa.Column('instance_id', sa.String(100), nullable=False, server_default='local'),
            sa.Column('config', sa.JSON(), nullable=True),
            sa.Column('installed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            
            # BaseEntity
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        print("  ✅ Created plugin_installations table")

    if 'plugin_reviews' not in existing_tables:
        op.create_table(
            'plugin_reviews',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('plugin_id', sa.String(36), sa.ForeignKey('plugins.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('review_text', sa.String(1000), nullable=True),
            
            # BaseEntity
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        print("  ✅ Created plugin_reviews table")

    # =========================================================================
    # 5. Mobile API tables (Phase 11.4)
    # =========================================================================
    if 'device_tokens' not in existing_tables:
        op.create_table(
            'device_tokens',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('platform', sa.String(20), nullable=False),
            sa.Column('token', sa.String(255), nullable=False, unique=True),
            sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            
            # BaseEntity
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        print("  ✅ Created device_tokens table")

    print("\n" + "=" * 70)
    print("✅ Migration 005_phase11_ecosystem completed successfully!")
    print("=" * 70)

def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    print("🔄 Starting downgrade of 005_phase11_ecosystem...")

    if 'device_tokens' in existing_tables:
        op.drop_table('device_tokens')
    if 'plugin_reviews' in existing_tables:
        op.drop_table('plugin_reviews')
    if 'plugin_installations' in existing_tables:
        op.drop_table('plugin_installations')
    if 'plugins' in existing_tables:
        op.drop_table('plugins')
    if 'federated_votes' in existing_tables:
        op.drop_table('federated_votes')
    if 'federated_tasks' in existing_tables:
        op.drop_table('federated_tasks')
    if 'federated_instances' in existing_tables:
        op.drop_table('federated_instances')
    if 'delegations' in existing_tables:
        op.drop_table('delegations')

    user_columns = {col['name'] for col in inspector.get_columns('users')}
    if 'role_expires_at' in user_columns:
        op.drop_column('users', 'role_expires_at')
    if 'delegated_by_id' in user_columns:
        op.drop_constraint('fk_users_delegated_by_id', 'users', type_='foreignkey')
        op.drop_column('users', 'delegated_by_id')
    if 'role' in user_columns:
        op.drop_column('users', 'role')

    print("✅ Downgrade 005_phase11_ecosystem completed")
