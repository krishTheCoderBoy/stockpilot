import uuid
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.purchase_orders.models import POStatus


class POItemCreate(BaseModel):
    product_id: uuid.UUID
    ordered_quantity: Decimal
    unit_price: Decimal


class POItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    ordered_quantity: Decimal
    received_quantity: Decimal
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderCreate(BaseModel):
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    notes: str | None = None
    items: list[POItemCreate] = Field(min_length=1)


class PurchaseOrderOut(BaseModel):
    id: uuid.UUID
    po_number: str
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    status: POStatus
    created_by: uuid.UUID
    approved_by: uuid.UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    items: list[POItemOut]

    
class ReceiveItemRequest(BaseModel):
    po_item_id: uuid.UUID
    quantity: Decimal


class ReceiveRequest(BaseModel):
    items: list[ReceiveItemRequest] = Field(min_length=1)

    model_config = ConfigDict(from_attributes=True)