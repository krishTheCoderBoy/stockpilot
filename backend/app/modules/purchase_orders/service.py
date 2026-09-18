import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.purchase_orders.models import PurchaseOrder, PurchaseOrderItem, POStatus
from app.modules.purchase_orders.repository import PurchaseOrderRepository
from app.modules.purchase_orders.schemas import PurchaseOrderCreate

# Explicit allowed transitions — the state machine, as data, not scattered if/else
ALLOWED_TRANSITIONS = {
    POStatus.DRAFT: {POStatus.SUBMITTED},
    POStatus.SUBMITTED: {POStatus.APPROVED, POStatus.DRAFT},
    POStatus.APPROVED: {POStatus.ORDERED},
    POStatus.ORDERED: {POStatus.PARTIALLY_RECEIVED, POStatus.RECEIVED},
    POStatus.PARTIALLY_RECEIVED: {POStatus.RECEIVED},
    POStatus.RECEIVED: {POStatus.CLOSED},
    POStatus.CLOSED: set(),
}


class PurchaseOrderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PurchaseOrderRepository(db)

    def _generate_po_number(self) -> str:
        return f"PO-{uuid.uuid4().hex[:8].upper()}"

    def _transition(self, po: PurchaseOrder, new_status: POStatus) -> None:
        allowed = ALLOWED_TRANSITIONS.get(po.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {po.status.value} to {new_status.value}",
            )
        po.status = new_status
        po.updated_at = datetime.now(timezone.utc)

    def create_po(self, payload: PurchaseOrderCreate, created_by) -> PurchaseOrder:
        po = PurchaseOrder(
            po_number=self._generate_po_number(),
            supplier_id=payload.supplier_id,
            warehouse_id=payload.warehouse_id,
            notes=payload.notes,
            created_by=created_by,
            status=POStatus.DRAFT,
        )
        for item in payload.items:
            po.items.append(
                PurchaseOrderItem(
                    product_id=item.product_id,
                    ordered_quantity=item.ordered_quantity,
                    unit_price=item.unit_price,
                )
            )
        return self.repo.create(po)

    def get_po(self, po_id) -> PurchaseOrder:
        po = self.repo.get_by_id(po_id)
        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
        return po

    def list_pos(self, skip: int = 0, limit: int = 50) -> list[PurchaseOrder]:
        return self.repo.list_all(skip, limit)

    def submit(self, po_id) -> PurchaseOrder:
        po = self.get_po(po_id)
        self._transition(po, POStatus.SUBMITTED)
        return self.repo.save(po)

    def approve(self, po_id, approved_by) -> PurchaseOrder:
        po = self.get_po(po_id)
        self._transition(po, POStatus.APPROVED)
        po.approved_by = approved_by
        return self.repo.save(po)

    def mark_ordered(self, po_id) -> PurchaseOrder:
        po = self.get_po(po_id)
        self._transition(po, POStatus.ORDERED)
        return self.repo.save(po)

    def close(self, po_id) -> PurchaseOrder:
        po = self.get_po(po_id)
        self._transition(po, POStatus.CLOSED)
        return self.repo.save(po)