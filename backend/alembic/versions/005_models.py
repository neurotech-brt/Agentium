"""add index on user_model_configs user_id and is_default

Revision ID: 005_models
Revises: 004_webhooks
Create Date: 2026-03-16 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic
revision = '005_models'
down_revision = '004_webhooks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        index_name  = 'ix_user_model_configs_user_default',
        table_name  = 'user_model_configs',
        columns     = ['user_id', 'is_default'],
        unique      = False,
    )


def downgrade() -> None:
    op.drop_index(
        index_name = 'ix_user_model_configs_user_default',
        table_name = 'user_model_configs',
    )