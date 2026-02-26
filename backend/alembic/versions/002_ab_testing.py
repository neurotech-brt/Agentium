"""Add A/B testing framework tables

Revision ID: 004_ab_testing
Revises: 003_user_preferences
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_ab_testing'
down_revision = '001_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types (PostgreSQL) - using raw SQL with IF NOT EXISTS guards
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'experiment_status') THEN
                CREATE TYPE experiment_status AS ENUM (
                    'draft', 'pending', 'running', 'completed', 'failed', 'cancelled'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'run_status') THEN
                CREATE TYPE run_status AS ENUM (
                    'pending', 'running', 'completed', 'failed'
                );
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_complexity') THEN
                CREATE TYPE task_complexity AS ENUM (
                    'simple', 'medium', 'complex'
                );
            END IF;
        END $$;
    """)

    # ── experiments ──────────────────────────────────────────────────────────
    op.create_table(
        'experiments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('task_template', sa.Text(), nullable=False),
        sa.Column('system_prompt', sa.Text()),
        sa.Column('test_iterations', sa.Integer(), server_default='1'),
        sa.Column(
            'status',
            postgresql.ENUM(
                'draft', 'pending', 'running', 'completed', 'failed', 'cancelled',
                name='experiment_status', create_type=False
            ),
            server_default='draft'
        ),
        sa.Column('created_by', sa.String(50), server_default='sovereign'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
    )
    op.create_index('idx_experiments_status', 'experiments', ['status'])
    op.create_index('idx_experiments_created_at', 'experiments', ['created_at'])

    # ── experiment_runs ───────────────────────────────────────────────────────
    op.create_table(
        'experiment_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('experiment_id', sa.String(36), sa.ForeignKey('experiments.id', ondelete='CASCADE')),
        sa.Column('config_id', sa.String(36), sa.ForeignKey('user_model_configs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('model_name', sa.String(100)),
        sa.Column('iteration_number', sa.Integer(), server_default='1'),
        sa.Column(
            'status',
            postgresql.ENUM(
                'pending', 'running', 'completed', 'failed',
                name='run_status', create_type=False
            ),
            server_default='pending'
        ),
        sa.Column('output_text', sa.Text()),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('latency_ms', sa.Integer()),
        sa.Column('cost_usd', sa.Float()),
        sa.Column('critic_plan_score', sa.Float()),
        sa.Column('critic_code_score', sa.Float()),
        sa.Column('critic_output_score', sa.Float()),
        sa.Column('overall_quality_score', sa.Float()),
        sa.Column('critic_feedback', postgresql.JSON()),
        sa.Column('constitutional_violations', sa.Integer(), server_default='0'),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('error_message', sa.Text()),
    )
    op.create_index('idx_experiment_runs_experiment_id', 'experiment_runs', ['experiment_id'])
    op.create_index('idx_experiment_runs_config_id', 'experiment_runs', ['config_id'])
    op.create_index('idx_experiment_runs_status', 'experiment_runs', ['status'])

    # ── experiment_results ────────────────────────────────────────────────────
    op.create_table(
        'experiment_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('experiment_id', sa.String(36), sa.ForeignKey('experiments.id', ondelete='CASCADE')),
        sa.Column('winner_config_id', sa.String(36), sa.ForeignKey('user_model_configs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('winner_model_name', sa.String(100)),
        sa.Column('selection_reason', sa.Text()),
        sa.Column('model_comparisons', postgresql.JSON()),
        sa.Column('statistical_significance', sa.Float()),
        sa.Column('recommended_for_similar', sa.Boolean(), server_default='false'),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_experiment_results_experiment_id', 'experiment_results', ['experiment_id'])

    # ── model_performance_cache ───────────────────────────────────────────────
    op.create_table(
        'model_performance_cache',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_category', sa.String(50)),
        sa.Column(
            'task_complexity',
            postgresql.ENUM(
                'simple', 'medium', 'complex',
                name='task_complexity', create_type=False
            ),
        ),
        sa.Column('best_config_id', sa.String(36), sa.ForeignKey('user_model_configs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('best_model_name', sa.String(100)),
        sa.Column('avg_latency_ms', sa.Integer()),
        sa.Column('avg_cost_usd', sa.Float()),
        sa.Column('avg_quality_score', sa.Float()),
        sa.Column('success_rate', sa.Float()),
        sa.Column('derived_from_experiment_id', sa.String(36), sa.ForeignKey('experiments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('sample_size', sa.Integer()),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_performance_cache_category', 'model_performance_cache', ['task_category'])
    op.create_index('idx_performance_cache_quality', 'model_performance_cache', ['avg_quality_score'])


def downgrade():
    op.drop_table('model_performance_cache')
    op.drop_table('experiment_results')
    op.drop_table('experiment_runs')
    op.drop_table('experiments')

    op.execute('DROP TYPE IF EXISTS task_complexity CASCADE')
    op.execute('DROP TYPE IF EXISTS run_status CASCADE')
    op.execute('DROP TYPE IF EXISTS experiment_status CASCADE')