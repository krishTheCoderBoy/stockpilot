import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel
class PurchaseOrderCreated(BaseModel):
    event_id: uuid.UUID
    event_type: Literal["PurchaseOrderCreated"] = "PurchaseOrderCreated"
    occurred_at: datetime
    po_id: uuid.UUID
    po_number: str
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
class PurchaseOrderApproved(BaseModel):
    event_id: uuid.UUID
    event_type: Literal["PurchaseOrderApproved"] = "PurchaseOrderApproved"
    occurred_at: datetime
    po_id: uuid.UUID
    approved_by: uuid.UUID
class ReceivePurchaseOrderItems(BaseModel):
    event_id: uuid.UUID
    event_type: Literal["ReceivePurchaseOrderItems"] = "ReceivePurchaseOrderItems"
    occurred_at: datetime
    po_id: uuid.UUID
    po_number: str
    warehouse_id: uuid.UUID
    performed_by: uuid.UUID
    items: list[dict]
class PurchaseOrderReceived(BaseModel):
    event_id: uuid.UUID
    event_type: Literal["PurchaseOrderReceived"] = "PurchaseOrderReceived"
    occurred_at: datetime
    po_id: uuid.UUID
    fully_received: bool
