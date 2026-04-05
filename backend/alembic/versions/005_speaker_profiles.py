"""add speaker_profiles

Revision ID: 005_speaker_profiles
Revises: 004_event_triggers
Create Date: 2026-04-05 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_speaker_profiles'
down_revision = '004_event_triggers'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('speaker_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=False),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_speaker_profiles_id'), 'speaker_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_speaker_profiles_user_id'), 'speaker_profiles', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_speaker_profiles_user_id'), table_name='speaker_profiles')
    op.drop_index(op.f('ix_speaker_profiles_id'), table_name='speaker_profiles')
    op.drop_table('speaker_profiles')
