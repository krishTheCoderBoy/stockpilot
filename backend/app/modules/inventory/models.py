import uuid
from datetime import datetime

from sqlalchemy import Column, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    on_hand_quantity = Column(Numeric(14, 2), nullable=False, default=0)
    reserved_quantity = Column(Numeric(14, 2), nullable=False, default=0)
    average_unit_cost = Column(Numeric(12, 2), nullable=False, default=0)
    safety_stock_override = Column(Numeric(14, 2), nullable=True)
    last_movement_at = Column(DateTime(timezone=True), nullable=True)