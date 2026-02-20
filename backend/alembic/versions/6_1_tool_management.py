"""
Phase 6.1 Tool Management Migration
Adds:
  - tool_staging        (extracted + enhanced from inline class)
  - tool_versions       (versioning & rollback)
  - tool_usage_logs     (analytics)
  - tool_marketplace_listings (marketplace)

Revision: 6_1_tool_management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = None
down_revision = None   # Set to your latest migration revision
branch_labels = None
depends_on = None


def upgrade():

    # ──────────────────────────────────────────────────────────────
    # tool_staging
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        'tool_staging',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tool_name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('proposed_by_agentium_id', sa.String(10), nullable=False, index=True),
        sa.Column('tool_path', sa.String(500), nullable=False),
        sa.Column('request_json', sa.Text, nullable=False),
        sa.Column('requires_vote', sa.Boolean, default=True),
        sa.Column('voting_id', sa.String(36), nullable=True),
        sa.Column('status', sa.String(50), default='pending_approval', index=True),
        sa.Column('current_version', sa.Integer, default=1, nullable=False),
        sa.Column('activated_at', sa.DateTime, nullable=True),
        sa.Column('deprecated_at', sa.DateTime, nullable=True),
        sa.Column('sunset_at', sa.DateTime, nullable=True),
        sa.Column('deprecated_by_agentium_id', sa.String(10), nullable=True),
        sa.Column('deprecation_reason', sa.Text, nullable=True),
        sa.Column('replacement_tool_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.String(1), default='Y'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )

    # ──────────────────────────────────────────────────────────────
    # tool_versions
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        'tool_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tool_name', sa.String(100), nullable=False, index=True),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('version_tag', sa.String(20), nullable=False),
        sa.Column('code_snapshot', sa.Text, nullable=False),
        sa.Column('tool_path', sa.String(500), nullable=False),
        sa.Column('authored_by_agentium_id', sa.String(10), nullable=False),
        sa.Column('change_summary', sa.Text, nullable=True),
        sa.Column('approved_by_voting_id', sa.String(36), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('is_active', sa.Boolean, default=False),
        sa.Column('is_rolled_back', sa.Boolean, default=False),
        sa.Column('rolled_back_from_version', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )
    op.create_index(
        'ix_tool_versions_name_number',
        'tool_versions',
        ['tool_name', 'version_number'],
        unique=True,
    )

    # ──────────────────────────────────────────────────────────────
    # tool_usage_logs
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        'tool_usage_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tool_name', sa.String(100), nullable=False, index=True),
        sa.Column('tool_version', sa.Integer, nullable=False, default=1),
        sa.Column('called_by_agentium_id', sa.String(10), nullable=False, index=True),
        sa.Column('task_id', sa.String(36), nullable=True, index=True),
        sa.Column('success', sa.Boolean, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('latency_ms', sa.Float, nullable=True),
        sa.Column('input_hash', sa.String(64), nullable=True),
        sa.Column('output_size_bytes', sa.Integer, nullable=True),
        sa.Column('invoked_at', sa.DateTime, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index(
        'ix_tool_usage_tool_invoked',
        'tool_usage_logs',
        ['tool_name', 'invoked_at'],
    )
    op.create_index(
        'ix_tool_usage_agent_tool',
        'tool_usage_logs',
        ['called_by_agentium_id', 'tool_name'],
    )

    # ──────────────────────────────────────────────────────────────
    # tool_marketplace_listings
    # ──────────────────────────────────────────────────────────────
    op.create_table(
        'tool_marketplace_listings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tool_name', sa.String(100), nullable=False, index=True),
        sa.Column('version_tag', sa.String(20), nullable=False),
        sa.Column('publisher_instance_id', sa.String(100), nullable=False),
        sa.Column('published_by_agentium_id', sa.String(10), nullable=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('tags', sa.JSON, default=list),
        sa.Column('code_snapshot', sa.Text, nullable=False),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('parameters_schema', sa.JSON, default=dict),
        sa.Column('authorized_tiers', sa.JSON, default=list),
        sa.Column('is_local', sa.Boolean, default=True),
        sa.Column('is_imported', sa.Boolean, default=False),
        sa.Column('import_source_url', sa.String(500), nullable=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('trust_score', sa.Float, default=0.0),
        sa.Column('download_count', sa.Integer, default=0),
        sa.Column('rating_sum', sa.Float, default=0.0),
        sa.Column('rating_count', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('published_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('yanked_at', sa.DateTime, nullable=True),
        sa.Column('yank_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )


def downgrade():
    op.drop_table('tool_marketplace_listings')
    op.drop_index('ix_tool_usage_agent_tool', table_name='tool_usage_logs')
    op.drop_index('ix_tool_usage_tool_invoked', table_name='tool_usage_logs')
    op.drop_table('tool_usage_logs')
    op.drop_index('ix_tool_versions_name_number', table_name='tool_versions')
    op.drop_table('tool_versions')
    op.drop_table('tool_staging')