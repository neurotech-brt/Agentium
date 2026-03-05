"""
Add missing columns: audit_logs.screenshot_url and critique_reviews.learning_extracted

Revision ID: 007_audit_screenshot_url
Revises: 006_notification_preferences
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '007_audit_screenshot_url'
down_revision = '006_notification_preferences'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    print("🚀 Starting migration 007_audit_screenshot_url...")

    # ── 1. audit_logs.screenshot_url ─────────────────────────────────────────
    audit_cols = {col['name'] for col in inspector.get_columns('audit_logs')}
    if 'screenshot_url' not in audit_cols:
        op.add_column(
            'audit_logs',
            sa.Column('screenshot_url', sa.String(500), nullable=True),
        )
        print("  ✅ Added audit_logs.screenshot_url")
    else:
        print("  ℹ️  audit_logs.screenshot_url already exists — skipping")

    # ── 2. critique_reviews.learning_extracted ────────────────────────────────
    existing_tables = set(inspector.get_table_names())
    if 'critique_reviews' in existing_tables:
        critique_cols = {col['name'] for col in inspector.get_columns('critique_reviews')}
        if 'learning_extracted' not in critique_cols:
            op.add_column(
                'critique_reviews',
                sa.Column('learning_extracted', sa.Boolean(), nullable=False,
                          server_default='false'),
            )
            print("  ✅ Added critique_reviews.learning_extracted")
        else:
            print("  ℹ️  critique_reviews.learning_extracted already exists — skipping")
    else:
        print("  ⚠️  critique_reviews table not found — skipping")

    print("\n" + "=" * 70)
    print("✅ Migration 007_audit_screenshot_url completed successfully!")
    print("=" * 70)


def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    print("🔄 Starting downgrade of 007_audit_screenshot_url...")

    existing_tables = set(inspector.get_table_names())

    if 'critique_reviews' in existing_tables:
        critique_cols = {col['name'] for col in inspector.get_columns('critique_reviews')}
        if 'learning_extracted' in critique_cols:
            op.drop_column('critique_reviews', 'learning_extracted')
            print("  ✅ Dropped critique_reviews.learning_extracted")

    audit_cols = {col['name'] for col in inspector.get_columns('audit_logs')}
    if 'screenshot_url' in audit_cols:
        op.drop_column('audit_logs', 'screenshot_url')
        print("  ✅ Dropped audit_logs.screenshot_url")

    print("✅ Downgrade 007_audit_screenshot_url completed")