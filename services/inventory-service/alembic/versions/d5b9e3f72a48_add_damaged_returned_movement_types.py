"""add DAMAGED and RETURNED movement types

Downgrade is a no-op: PostgreSQL cannot drop enum values, and rows may already use
them. Older code simply never reads the extra values.
"""
from alembic import op

revision = "d5b9e3f72a48"
down_revision = "b3f5a7c91d24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Committed outside the migration transaction so the values are usable immediately
    # on older Postgres versions; IF NOT EXISTS keeps reruns safe.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE movement_type ADD VALUE IF NOT EXISTS 'DAMAGED'")
        op.execute("ALTER TYPE movement_type ADD VALUE IF NOT EXISTS 'RETURNED'")


def downgrade() -> None:
    pass
