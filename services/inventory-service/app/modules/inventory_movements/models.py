import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, Numeric, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class MovementType(str, enum.Enum):
    RECEIVE = "RECEIVE"
    ISSUE = "ISSUE"
    ADJUSTMENT_INCREASE = "ADJUSTMENT_INCREASE"
    ADJUSTMENT_DECREASE = "ADJUSTMENT_DECREASE"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"


class ReferenceType(str, enum.Enum):
    MANUAL = "MANUAL"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    TRANSFER = "TRANSFER"


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    movement_type = Column(SAEnum(MovementType, name="movement_type"), nullable=False)
    quantity = Column(Numeric(14, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=True)
    reference_type = Column(SAEnum(ReferenceType, name="reference_type"), nullable=False, default=ReferenceType.MANUAL)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)