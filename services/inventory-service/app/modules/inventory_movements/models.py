import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, Computed, Numeric, DateTime, ForeignKey, Index, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID

from app.core.database import Base


class MovementType(str, enum.Enum):
    RECEIVE = "RECEIVE"
    ISSUE = "ISSUE"
    ADJUSTMENT_INCREASE = "ADJUSTMENT_INCREASE"
    ADJUSTMENT_DECREASE = "ADJUSTMENT_DECREASE"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    # Kept apart from ISSUE/ADJUSTMENT so demand forecasting can use ISSUE as real demand
    # and treat write-offs (DAMAGED) and customer returns (RETURNED) separately.
    DAMAGED = "DAMAGED"
    RETURNED = "RETURNED"


class ReferenceType(str, enum.Enum):
    MANUAL = "MANUAL"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    TRANSFER = "TRANSFER"


# Must stay identical to the expression in migration e6c1f4a83b59. Only the movement's own
# notes: a generated column cannot read other tables, and reference_type is an enum whose
# text cast is not immutable, which Postgres requires here. Receipts carry the PO number in
# their notes, so purchase-order references are still searchable.
MOVEMENT_SEARCH_EXPRESSION = "setweight(to_tsvector('english', coalesce(notes, '')), 'A')"


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        Index("idx_movements_search_vector", "search_vector", postgresql_using="gin"),
        # Demand-history queries filter on movement_type = ISSUE plus a date range, either
        # for one product (first index) or across all products (second).
        Index("ix_movements_product_type_created", "product_id", "movement_type", "created_at"),
        Index("ix_movements_type_created", "movement_type", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    movement_type = Column(SAEnum(MovementType, name="movement_type"), nullable=False)
    quantity = Column(Numeric(14, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=True)
    reference_type = Column(SAEnum(ReferenceType, name="reference_type"), nullable=False, default=ReferenceType.MANUAL)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    # Actor identity is supplied by the verified JWT; users are owned by auth_db.
    performed_by = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    search_vector = Column(TSVECTOR, Computed(MOVEMENT_SEARCH_EXPRESSION, persisted=True))