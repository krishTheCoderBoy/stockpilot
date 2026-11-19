"""Initial owned schema baseline for isolated service database.

This used to call Base.metadata.create_all(), which made the baseline track the
*current* models: any column a later migration adds (search_vector first) was
already created by 0001 on a fresh database, and the later migration then failed
with a duplicate column. The DDL below is frozen to the schema at the service split,
which is exactly what create_all produced back then, so databases that already ran
the old 0001 are unaffected.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

warehouse_type = postgresql.ENUM("MAIN", "REGIONAL", "TRANSIT", name="warehouse_type", create_type=False)
movement_type = postgresql.ENUM(
    "RECEIVE", "ISSUE", "ADJUSTMENT_INCREASE", "ADJUSTMENT_DECREASE", "TRANSFER_OUT", "TRANSFER_IN",
    name="movement_type", create_type=False,
)
reference_type = postgresql.ENUM("MANUAL", "PURCHASE_ORDER", "TRANSFER", name="reference_type", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in (warehouse_type, movement_type, reference_type):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "product_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("parent_category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_categories.id"), nullable=True),
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_categories.id"), nullable=True),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_of_measure", sa.String(), nullable=False),
        sa.Column("reorder_point", sa.Numeric(12, 2), nullable=False),
        sa.Column("min_order_quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("max_stock_level", sa.Numeric(12, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("default_supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)

    op.create_table(
        "warehouses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("capacity", sa.Numeric(14, 2), nullable=True),
        sa.Column("warehouse_type", warehouse_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_warehouses_code", "warehouses", ["code"], unique=True)

    op.create_table(
        "inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("on_hand_quantity", sa.Numeric(14, 2), nullable=False),
        sa.Column("reserved_quantity", sa.Numeric(14, 2), nullable=False),
        sa.Column("average_unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("safety_stock_override", sa.Numeric(14, 2), nullable=True),
        sa.Column("last_movement_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
    )

    op.create_table(
        "inventory_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("movement_type", movement_type, nullable=False),
        sa.Column("quantity", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("reference_type", reference_type, nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "inventory_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("batch_number", sa.String(), nullable=False),
        sa.Column("received_quantity", sa.Numeric(14, 2), nullable=False),
        sa.Column("remaining_quantity", sa.Numeric(14, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("movement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inventory_movements.id"), nullable=True),
    )
    op.create_index("ix_inventory_batches_batch_number", "inventory_batches", ["batch_number"])


def downgrade() -> None:
    op.drop_index("ix_inventory_batches_batch_number", table_name="inventory_batches")
    op.drop_table("inventory_batches")
    op.drop_table("inventory_movements")
    op.drop_table("inventory")
    op.drop_index("ix_warehouses_code", table_name="warehouses")
    op.drop_table("warehouses")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")
    op.drop_table("product_categories")
    bind = op.get_bind()
    for enum_type in (reference_type, movement_type, warehouse_type):
        enum_type.drop(bind, checkfirst=True)
