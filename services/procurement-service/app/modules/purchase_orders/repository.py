from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload
from app.modules.purchase_orders.models import POStatus, PurchaseOrder
class PurchaseOrderRepository:
    def __init__(self, db: Session): self.db = db
    def get_by_id(self, po_id): return self.db.query(PurchaseOrder).options(joinedload(PurchaseOrder.items)).filter(PurchaseOrder.id == po_id).first()
    def list_all(self, skip=0, limit=50, status=None):
        query = self.db.query(PurchaseOrder).options(joinedload(PurchaseOrder.items))
        if status is not None: query = query.filter(PurchaseOrder.status == status)
        return query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()
    def get_by_number(self, po_number: str): return self.db.query(PurchaseOrder).options(joinedload(PurchaseOrder.items)).filter(PurchaseOrder.po_number == po_number).first()
    def add(self, po): self.db.add(po); self.db.flush(); return po

    def count_by_status(self, statuses: set[POStatus]) -> int:
        return self.db.query(func.count(PurchaseOrder.id)).filter(PurchaseOrder.status.in_(statuses)).scalar() or 0
    def search(self, query: str, limit: int = 20) -> list[PurchaseOrder]:
        ts_query = func.websearch_to_tsquery("english", query)
        return (
            self.db.query(PurchaseOrder)
            # selectinload, not joinedload: a joined collection combined with LIMIT forces a
            # wrapping subquery around the ranked ordering.
            .options(selectinload(PurchaseOrder.items))
            .filter(PurchaseOrder.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank(PurchaseOrder.search_vector, ts_query).desc())
            .limit(limit)
            .all()
        )
