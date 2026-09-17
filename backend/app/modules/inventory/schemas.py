import uuid
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field


class InventoryOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    on_hand_quantity: Decimal
    reserved_quantity: Decimal
    average_unit_cost: Decimal
    safety_stock_override: Decimal | None
    last_movement_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def available_quantity(self) -> Decimal:
        return self.on_hand_quantity - self.reserved_quantity