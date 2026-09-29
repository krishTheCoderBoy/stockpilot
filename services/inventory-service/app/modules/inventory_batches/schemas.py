import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BatchOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    batch_number: str
    received_quantity: Decimal
    remaining_quantity: Decimal
    unit_cost: Decimal | None
    expiry_date: date | None
    received_at: datetime

    model_config = ConfigDict(from_attributes=True)