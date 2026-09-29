"""Create procurement owned tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "0001_procurement_tables"
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    status = postgresql.ENUM("DRAFT", "SUBMITTED", "APPROVED", "ORDERED", "PARTIALLY_RECEIVED", "RECEIVED", "CLOSED", name="po_status")
    status.create(op.get_bind(), checkfirst=True)
    op.create_table("suppliers", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("code", sa.String(), nullable=False), sa.Column("name", sa.String(), nullable=False), sa.Column("contact_person", sa.String()), sa.Column("email", sa.String()), sa.Column("phone", sa.String()), sa.Column("address", sa.Text()), sa.Column("lead_time_days", sa.Integer()), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_suppliers_code", "suppliers", ["code"], unique=True)
    op.create_table("purchase_orders", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("po_number", sa.String(), nullable=False), sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("suppliers.id"), nullable=False), sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("status", status, nullable=False), sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("approved_by", postgresql.UUID(as_uuid=True)), sa.Column("notes", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_purchase_orders_po_number", "purchase_orders", ["po_number"], unique=True)
    op.create_table("purchase_order_items", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchase_orders.id"), nullable=False), sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("ordered_quantity", sa.Numeric(14,2), nullable=False), sa.Column("received_quantity", sa.Numeric(14,2), nullable=False, server_default="0"), sa.Column("unit_price", sa.Numeric(12,2), nullable=False))
def downgrade() -> None:
    op.drop_table("purchase_order_items")
    op.drop_index("ix_purchase_orders_po_number", table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.drop_index("ix_suppliers_code", table_name="suppliers")
    op.drop_table("suppliers")
    postgresql.ENUM(name="po_status").drop(op.get_bind(), checkfirst=True)
