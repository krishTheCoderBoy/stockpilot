import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class DomainEvent(BaseModel):
    event_id: uuid.UUID
    event_type: str
    occurred_at: datetime


class PurchaseOrderCreated(DomainEvent):
    event_type: Literal["PurchaseOrderCreated"] = "PurchaseOrderCreated"
    po_id: uuid.UUID
    po_number: str
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID


class PurchaseOrderApproved(DomainEvent):
    event_type: Literal["PurchaseOrderApproved"] = "PurchaseOrderApproved"
    po_id: uuid.UUID
    approved_by: uuid.UUID


class PurchaseOrderReceived(DomainEvent):
    event_type: Literal["PurchaseOrderReceived"] = "PurchaseOrderReceived"
    po_id: uuid.UUID
    fully_received: bool


class InventoryUpdated(DomainEvent):
    event_type: Literal["InventoryUpdated"] = "InventoryUpdated"
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    on_hand_quantity: Decimal


class InventoryTransferred(DomainEvent):
    event_type: Literal["InventoryTransferred"] = "InventoryTransferred"
    product_id: uuid.UUID
    source_warehouse_id: uuid.UUID
    destination_warehouse_id: uuid.UUID
    quantity: Decimal


class StockLow(DomainEvent):
    event_type: Literal["StockLow"] = "StockLow"
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    on_hand_quantity: Decimal
    reorder_point: Decimal