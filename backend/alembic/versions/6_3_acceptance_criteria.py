"""
Phase 6.3 — Pre-Declared Acceptance Criteria Migration
Adds `acceptance_criteria` and `veto_authority` to the tasks table.
Also adds `criteria_results` to critique_reviews for per-criterion outcomes.

Revision: 6_3_acceptance_criteria
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '6_3_acceptance_criteria'
down_revision = '6_1_tool_management'
branch_labels = None
depends_on = None


def upgrade():
    # ── tasks table ──────────────────────────────────────────────────────────
    # acceptance_criteria: JSON array of AcceptanceCriterion dicts
    # veto_authority:      which critic type is the designated validator
    op.add_column(
        'tasks',
        sa.Column(
            'acceptance_criteria',
            sa.JSON,
            nullable=True,
            comment=(
                'JSON array of AcceptanceCriterion objects. '
                'Structure: [{metric, threshold, validator, is_mandatory, description}]'
            )
        )
    )
    op.add_column(
        'tasks',
        sa.Column(
            'veto_authority',
            sa.String(20),
            nullable=True,
            comment='Critic type that has veto authority: code | output | plan'
        )
    )

    # ── critique_reviews table ───────────────────────────────────────────────
    # criteria_results: per-criterion pass/fail outcomes stored after review
    op.add_column(
        'critique_reviews',
        sa.Column(
            'criteria_results',
            sa.JSON,
            nullable=True,
            comment=(
                'JSON array of per-criterion results. '
                'Structure: [{metric, passed, actual_value, threshold, is_mandatory}]'
            )
        )
    )
    op.add_column(
        'critique_reviews',
        sa.Column(
            'criteria_evaluated',
            sa.Integer,
            nullable=True,
            comment='Total number of criteria evaluated in this review'
        )
    )
    op.add_column(
        'critique_reviews',
        sa.Column(
            'criteria_passed',
            sa.Integer,
            nullable=True,
            comment='Number of criteria that passed'
        )
    )


def downgrade():
    op.drop_column('critique_reviews', 'criteria_passed')
    op.drop_column('critique_reviews', 'criteria_evaluated')
    op.drop_column('critique_reviews', 'criteria_results')
    op.drop_column('tasks', 'veto_authority')
    op.drop_column('tasks', 'acceptance_criteria')