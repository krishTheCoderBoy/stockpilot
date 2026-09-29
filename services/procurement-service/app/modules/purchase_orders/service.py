import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.modules.purchase_orders.models import PurchaseOrder, PurchaseOrderItem, POStatus
from app.modules.suppliers.repository import SupplierRepository
from app.modules.purchase_orders.repository import PurchaseOrderRepository
from app.modules.purchase_orders.schemas import PurchaseOrderCreate, ReceiveRequest
from app.core.events.publisher import publish_event
from app.core.events.schemas import PurchaseOrderCreated, PurchaseOrderApproved, PurchaseOrderReceived, ReceivePurchaseOrderItems
from app.core.inventory_client import validate_inventory_resource
ALLOWED_TRANSITIONS = {POStatus.DRAFT:{POStatus.SUBMITTED}, POStatus.SUBMITTED:{POStatus.APPROVED,POStatus.DRAFT}, POStatus.APPROVED:{POStatus.ORDERED}, POStatus.ORDERED:{POStatus.PARTIALLY_RECEIVED,POStatus.RECEIVED}, POStatus.PARTIALLY_RECEIVED:{POStatus.RECEIVED}, POStatus.RECEIVED:{POStatus.CLOSED}, POStatus.CLOSED:set()}
class PurchaseOrderService:
    def __init__(self, db: Session): self.db, self.repo, self.suppliers = db, PurchaseOrderRepository(db), SupplierRepository(db)
    def _get(self, po_id):
        po=self.repo.get_by_id(po_id)
        if not po: raise HTTPException(status_code=404, detail="Purchase order not found")
        return po
    def _save(self, po):
        try: self.db.commit(); self.db.refresh(po); return po
        except Exception: self.db.rollback(); raise
    def _transition(self, po, new_status):
        if new_status not in ALLOWED_TRANSITIONS.get(po.status,set()): raise HTTPException(status_code=400, detail=f"Cannot transition from {po.status.value} to {new_status.value}")
        po.status, po.updated_at = new_status, datetime.now(timezone.utc)
    def create_po(self, payload: PurchaseOrderCreate, created_by, authorization: str):
        supplier = self.suppliers.get_by_id(payload.supplier_id)
        if not supplier or not supplier.is_active: raise HTTPException(status_code=400, detail="Supplier not found or inactive")
        validate_inventory_resource("warehouses", str(payload.warehouse_id), authorization)
        for item in payload.items: validate_inventory_resource("products", str(item.product_id), authorization)
        po=PurchaseOrder(po_number=f"PO-{uuid.uuid4().hex[:8].upper()}",supplier_id=payload.supplier_id,warehouse_id=payload.warehouse_id,notes=payload.notes,created_by=created_by,status=POStatus.DRAFT)
        po.items=[PurchaseOrderItem(product_id=i.product_id,ordered_quantity=i.ordered_quantity,unit_price=i.unit_price) for i in payload.items]
        try:
            self.repo.add(po); self.db.commit(); self.db.refresh(po)
        except Exception: self.db.rollback(); raise
        publish_event(PurchaseOrderCreated(event_id=uuid.uuid4(),occurred_at=datetime.now(timezone.utc),po_id=po.id,po_number=po.po_number,supplier_id=po.supplier_id,warehouse_id=po.warehouse_id))
        return po
    def get_po(self, po_id): return self._get(po_id)
    def list_pos(self, skip=0, limit=50): return self.repo.list_all(skip,limit)
    def submit(self, po_id):
        po=self._get(po_id); self._transition(po,POStatus.SUBMITTED); return self._save(po)
    def approve(self, po_id, approved_by):
        po=self._get(po_id); self._transition(po,POStatus.APPROVED); po.approved_by=approved_by; self._save(po)
        publish_event(PurchaseOrderApproved(event_id=uuid.uuid4(),occurred_at=datetime.now(timezone.utc),po_id=po.id,approved_by=approved_by)); return po
    def mark_ordered(self, po_id):
        po=self._get(po_id); self._transition(po,POStatus.ORDERED); return self._save(po)
    def close(self, po_id):
        po=self._get(po_id); self._transition(po,POStatus.CLOSED); return self._save(po)
    def receive(self, po_id, payload: ReceiveRequest, performed_by):
        po=self._get(po_id)
        if po.status not in {POStatus.ORDERED,POStatus.PARTIALLY_RECEIVED}: raise HTTPException(status_code=400,detail=f"Cannot receive against a PO in status {po.status.value}")
        by_id={i.id:i for i in po.items}; event_items=[]
        for entry in payload.items:
            item=by_id.get(entry.po_item_id)
            if not item: raise HTTPException(status_code=400,detail=f"PO item {entry.po_item_id} does not belong to this purchase order")
            remaining=item.ordered_quantity-item.received_quantity
            if entry.quantity <= 0 or entry.quantity > remaining: raise HTTPException(status_code=400,detail=f"Received quantity must be positive and no more than remaining quantity ({remaining})")
            item.received_quantity += entry.quantity
            event_items.append({"po_item_id":str(item.id),"product_id":str(item.product_id),"quantity":str(entry.quantity),"unit_cost":str(item.unit_price)})
        fully=all(i.received_quantity>=i.ordered_quantity for i in po.items); self._transition(po,POStatus.RECEIVED if fully else POStatus.PARTIALLY_RECEIVED)
        try: self.db.commit(); self.db.refresh(po)
        except Exception: self.db.rollback(); raise
        # Procurement commits receipt bookkeeping before publishing; this keeps its own PO state authoritative and avoids a distributed DB transaction. The event consumer applies stock changes idempotently by event_id.
        publish_event(ReceivePurchaseOrderItems(event_id=uuid.uuid4(),occurred_at=datetime.now(timezone.utc),po_id=po.id,po_number=po.po_number,warehouse_id=po.warehouse_id,performed_by=performed_by,items=event_items))
        publish_event(PurchaseOrderReceived(event_id=uuid.uuid4(),occurred_at=datetime.now(timezone.utc),po_id=po.id,fully_received=fully)); return po
