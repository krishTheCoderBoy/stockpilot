import uuid
from datetime import datetime

from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
        # Last line of defence if a code path ever skips the service-level guards.
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_non_negative"),
        CheckConstraint("reserved_quantity <= on_hand_quantity", name="ck_inventory_reserved_within_on_hand"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    on_hand_quantity = Column(Numeric(14, 2), nullable=False, default=0)
    reserved_quantity = Column(Numeric(14, 2), nullable=False, default=0)
    average_unit_cost = Column(Numeric(12, 2), nullable=False, default=0)
    safety_stock_override = Column(Numeric(14, 2), nullable=True)
    last_movement_at = Column(DateTime(timezone=True), nullable=True)

    # The single definition of "available". As a hybrid it works on instances (guards,
    # API) and in SQL (low-stock queries), so the two can never drift apart.
    @hybrid_property
    def available_quantity(self) -> Decimal:
        return self.on_hand_quantity - self.reserved_quantity
