"""add stock reservations and reserved-quantity constraints

Reserved stock was never written before this revision, so every existing row has
reserved_quantity = 0 and the new CHECK constraints are satisfied by current data.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b3f5a7c91d24"
down_revision = "7d896323cfb5"
branch_labels = None
depends_on = None

reservation_status = postgresql.ENUM(
    "ACTIVE", "RELEASED", "FULFILLED", name="reservation_status", create_type=False
)


def upgrade() -> None:
    reservation_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "stock_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", reservation_status, nullable=False),
        sa.Column("reference_type", sa.String(), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fulfilled_quantity", sa.Numeric(14, 2), nullable=True),
        sa.Column(
            "fulfillment_movement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_movements.id"),
            nullable=True,
        ),
        sa.CheckConstraint("quantity > 0", name="ck_stock_reservations_quantity_positive"),
    )
    op.create_index(
        "ix_stock_reservations_product_warehouse_status",
        "stock_reservations",
        ["product_id", "warehouse_id", "status"],
    )

    op.create_check_constraint("ck_inventory_reserved_non_negative", "inventory", "reserved_quantity >= 0")
    op.create_check_constraint(
        "ck_inventory_reserved_within_on_hand", "inventory", "reserved_quantity <= on_hand_quantity"
    )


def downgrade() -> None:
    op.drop_constraint("ck_inventory_reserved_within_on_hand", "inventory", type_="check")
    op.drop_constraint("ck_inventory_reserved_non_negative", "inventory", type_="check")
    op.drop_index("ix_stock_reservations_product_warehouse_status", table_name="stock_reservations")
    op.drop_table("stock_reservations")
    reservation_status.drop(op.get_bind(), checkfirst=True)
