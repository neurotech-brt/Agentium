"""Add missing agents.created_by_agentium_id column

Revision ID: 004_add_missing_agent_columns
Revises: 003_fix_schema_consistency
Create Date: 2026-02-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_missing_agent_columns'
down_revision = '003_fix_schema_consistency'
branch_labels = None
depends_on = None


def upgrade():
    # Add created_by_agentium_id to agents table
    op.add_column('agents', sa.Column('created_by_agentium_id', sa.String(length=10), nullable=True))


def downgrade():
    # Remove created_by_agentium_id from agents table
    op.drop_column('agents', 'created_by_agentium_id')
