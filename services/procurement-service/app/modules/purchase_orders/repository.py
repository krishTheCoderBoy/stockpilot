from sqlalchemy.orm import Session, joinedload
from app.modules.purchase_orders.models import PurchaseOrder
class PurchaseOrderRepository:
    def __init__(self, db: Session): self.db = db
    def get_by_id(self, po_id): return self.db.query(PurchaseOrder).options(joinedload(PurchaseOrder.items)).filter(PurchaseOrder.id == po_id).first()
    def list_all(self, skip=0, limit=50): return self.db.query(PurchaseOrder).options(joinedload(PurchaseOrder.items)).order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit).all()
    def add(self, po): self.db.add(po); self.db.flush(); return po
