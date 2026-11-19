"""add indexes for demand-history queries

Demand history filters the ledger on movement_type = 'ISSUE' and a created_at range,
for one product or for all of them. Without these two indexes that is a scan of the whole
append-only ledger. They cost some write speed on inserts; if that matters, the
(movement_type, created_at) one can be dropped and the all-products query will rely on
the product-leading index.
"""
from alembic import op

revision = "f7d2a9c15e80"
down_revision = "e6c1f4a83b59"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_movements_product_type_created",
        "inventory_movements",
        ["product_id", "movement_type", "created_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_movements_type_created",
        "inventory_movements",
        ["movement_type", "created_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_movements_type_created", table_name="inventory_movements", if_exists=True)
    op.drop_index("ix_movements_product_type_created", table_name="inventory_movements", if_exists=True)
