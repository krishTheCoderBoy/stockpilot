import uuid
from datetime import date, datetime

from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    batch_number = Column(String, nullable=False, index=True)
    received_quantity = Column(Numeric(14, 2), nullable=False)
    remaining_quantity = Column(Numeric(14, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=True)
    expiry_date = Column(Date, nullable=True)
    received_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    movement_id = Column(UUID(as_uuid=True), ForeignKey("inventory_movements.id"), nullable=True)