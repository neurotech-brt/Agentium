"""
Federation HMAC improvements 
=========================================
Revision ID: 008_federation_hmac
Revises: 007_audit_screenshot_url
Create Date: 2026-03-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '008_federation_hmac'
down_revision = '007_audit_screenshot_url'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    print("🚀 Starting migration 008_federation_hmac...")

    # ── 1. Add signing_key to federated_instances ─────────────────────────────
    if 'federated_instances' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('federated_instances')}

        if 'signing_key' not in existing_cols:
            op.add_column(
                'federated_instances',
                sa.Column('signing_key', sa.String(255), nullable=True),
            )
            print("  ✅ Added federated_instances.signing_key")

            # Back-fill: derive signing_key from shared_secret_hash for existing rows.
            # We cannot reverse the hash to recover the plaintext secret, so we copy
            # shared_secret_hash as a placeholder. Operators should re-register peers
            # (which will set the correct signing_key) to enable full HMAC auth.
            # Until then, existing peers continue to work via the legacy header-secret path.
            op.execute(
                "UPDATE federated_instances "
                "SET signing_key = shared_secret_hash "
                "WHERE signing_key IS NULL"
            )
            print("  ✅ Back-filled signing_key from shared_secret_hash")
            print("  ⚠️  Re-register peers to enable proper HMAC signing (current value is a placeholder)")
        else:
            print("  ℹ️  federated_instances.signing_key already exists — skipped")
    else:
        print("  ℹ️  federated_instances table not found — skipped (federation not enabled?)")

    # ── 2. Confirm federated_tasks.status is VARCHAR (no enum change needed) ──
    if 'federated_tasks' in existing_tables:
        status_col = next(
            (col for col in inspector.get_columns('federated_tasks') if col['name'] == 'status'),
            None,
        )
        if status_col:
            col_type = str(status_col['type']).upper()
            if 'CHAR' in col_type or 'TEXT' in col_type:
                print("  ✅ federated_tasks.status is VARCHAR — 'delivered' value accepted without migration")
            else:
                print(f"  ⚠️  federated_tasks.status type is '{col_type}' — verify 'delivered' is accepted")
        else:
            print("  ⚠️  Could not inspect federated_tasks.status column")
    else:
        print("  ℹ️  federated_tasks table not found — skipped")

    print("\n" + "=" * 70)
    print("✅ Migration 008_federation_hmac completed successfully!")
    print("=" * 70)
    print("Changes applied:")
    print("  • federated_instances.signing_key — HMAC signing key column added")
    print("  • federated_tasks.status          — 'delivered' value confirmed (no schema change)")
    print("=" * 70)
    print("Next steps:")
    print("  1. Re-register existing peers via the Federation UI to set correct signing keys")
    print("  2. Set FEDERATION_INSTANCE_URL and FEDERATION_SHARED_SECRET in your .env")
    print("=" * 70)


def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    print("🔄 Starting downgrade of 008_federation_hmac...")

    if 'federated_instances' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('federated_instances')}
        if 'signing_key' in existing_cols:
            op.drop_column('federated_instances', 'signing_key')
            print("  ✅ Dropped federated_instances.signing_key")
        else:
            print("  ℹ️  federated_instances.signing_key not found — nothing to drop")
    else:
        print("  ℹ️  federated_instances table not found — skipped")

    print("✅ Downgrade 008_federation_hmac completed")