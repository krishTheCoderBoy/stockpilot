"""add purchase order expected_date and CANCELLED status

Downgrade drops the column but cannot remove the CANCELLED enum value: PostgreSQL has
no ALTER TYPE ... DROP VALUE, and rebuilding the type would fail on cancelled rows.
The leftover value is harmless to older code, which never reads it.
"""
from alembic import op
import sqlalchemy as sa

revision = "c4a8d2e61f37"
down_revision = "016daf889d2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A new enum value cannot be used in the transaction that adds it on older Postgres
    # versions, so it is committed on its own first. IF NOT EXISTS keeps reruns safe.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE po_status ADD VALUE IF NOT EXISTS 'CANCELLED'")
    op.add_column("purchase_orders", sa.Column("expected_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("purchase_orders", "expected_date")
