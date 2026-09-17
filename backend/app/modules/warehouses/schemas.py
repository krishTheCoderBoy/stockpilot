import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.modules.warehouses.models import WarehouseType


class WarehouseCreate(BaseModel):
    code: str
    name: str
    city: str
    state: str
    country: str
    manager_id: uuid.UUID | None = None
    capacity: Decimal | None = None
    warehouse_type: WarehouseType = WarehouseType.MAIN


class WarehouseUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    manager_id: uuid.UUID | None = None
    capacity: Decimal | None = None
    warehouse_type: WarehouseType | None = None
    is_active: bool | None = None


class WarehouseOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    city: str
    state: str
    country: str
    manager_id: uuid.UUID | None
    capacity: Decimal | None
    warehouse_type: WarehouseType
    is_active: bool

    model_config = ConfigDict(from_attributes=True)