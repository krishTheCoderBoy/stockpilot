import uuid
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.purchase_orders.models import POStatus, PurchaseOrder, PurchaseOrderItem
from app.modules.suppliers.models import Supplier

# Orders that have been committed to but not fully received. SUBMITTED is excluded on
# purpose: it can still be rejected, so counting it would hide a real shortage.
INCOMING_STATUSES = {POStatus.APPROVED, POStatus.ORDERED, POStatus.PARTIALLY_RECEIVED}


class PlanningRepository:
    def __init__(self, db: Session):
        self.db = db

    def incoming_by_product(self, warehouse_id: uuid.UUID | None = None) -> dict[uuid.UUID, Decimal]:
        """Quantity still to arrive (ordered minus received) per product on open POs."""
        remaining = func.sum(PurchaseOrderItem.ordered_quantity - PurchaseOrderItem.received_quantity)
        query = (
            self.db.query(PurchaseOrderItem.product_id, remaining)
            .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.purchase_order_id)
            .filter(PurchaseOrder.status.in_(INCOMING_STATUSES))
        )
        if warehouse_id is not None:
            query = query.filter(PurchaseOrder.warehouse_id == warehouse_id)
        return {
            product_id: quantity
            for product_id, quantity in query.group_by(PurchaseOrderItem.product_id).all()
            if quantity and quantity > 0
        }

    def suppliers_by_id(self, supplier_ids: set[uuid.UUID]) -> dict[uuid.UUID, Supplier]:
        if not supplier_ids:
            return {}
        rows = self.db.query(Supplier).filter(Supplier.id.in_(supplier_ids)).all()
        return {supplier.id: supplier for supplier in rows}
