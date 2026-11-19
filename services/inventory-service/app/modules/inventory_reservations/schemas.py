import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.modules.inventory_reservations.models import ReservationStatus


class ReservationCreate(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: Decimal
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    notes: str | None = None


class ReservationOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: Decimal
    status: ReservationStatus
    reference_type: str | None
    reference_id: uuid.UUID | None
    notes: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    released_at: datetime | None
    fulfilled_quantity: Decimal | None
    fulfillment_movement_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)
