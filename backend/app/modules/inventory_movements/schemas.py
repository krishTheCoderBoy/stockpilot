import uuid
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.inventory_movements.models import MovementType, ReferenceType


class MovementCreate(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    movement_type: MovementType
    quantity: Decimal
    unit_cost: Decimal | None = None
    notes: str | None = None


class TransferCreate(BaseModel):
    product_id: uuid.UUID
    source_warehouse_id: uuid.UUID
    destination_warehouse_id: uuid.UUID
    quantity: Decimal
    notes: str | None = None


class MovementOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    movement_type: MovementType
    quantity: Decimal
    unit_cost: Decimal | None
    reference_type: ReferenceType
    reference_id: uuid.UUID | None
    performed_by: uuid.UUID | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)