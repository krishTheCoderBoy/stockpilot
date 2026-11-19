import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Numeric, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    FULFILLED = "FULFILLED"


class StockReservation(Base):
    """One explicit hold on stock. inventory.reserved_quantity is the sum of ACTIVE rows."""

    __tablename__ = "stock_reservations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_stock_reservations_quantity_positive"),
        Index("ix_stock_reservations_product_warehouse_status", "product_id", "warehouse_id", "status"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    quantity = Column(Numeric(14, 2), nullable=False)
    status = Column(SAEnum(ReservationStatus, name="reservation_status"), nullable=False, default=ReservationStatus.ACTIVE)
    # Free-form because no order module exists yet to own a typed reference.
    reference_type = Column(String, nullable=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(Text, nullable=True)
    # Actor identity is supplied by the verified JWT; users are owned by auth_db.
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=True)
    # Issued quantity may be below the reservation; the remainder returns to available
    # on fulfilment, and this column records that it happened.
    fulfilled_quantity = Column(Numeric(14, 2), nullable=True)
    fulfillment_movement_id = Column(UUID(as_uuid=True), ForeignKey("inventory_movements.id"), nullable=True)
