from sqlalchemy.orm import Session, joinedload

from app.modules.purchase_orders.models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, po_id) -> PurchaseOrder | None:
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.items))
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

    def get_by_po_number(self, po_number: str) -> PurchaseOrder | None:
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[PurchaseOrder]:
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.items))
            .order_by(PurchaseOrder.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, po: PurchaseOrder) -> PurchaseOrder:
        self.db.add(po)
        self.db.commit()
        self.db.refresh(po)
        return po

    def save(self, po: PurchaseOrder) -> PurchaseOrder:
        self.db.commit()
        self.db.refresh(po)
        return po