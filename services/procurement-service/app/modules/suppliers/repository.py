from sqlalchemy.orm import Session
from app.modules.suppliers.models import Supplier
class SupplierRepository:
    def __init__(self, db: Session): self.db = db
    def get_by_id(self, supplier_id): return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
    def get_by_code(self, code: str): return self.db.query(Supplier).filter(Supplier.code == code).first()
    def list_all(self, skip: int = 0, limit: int = 50): return self.db.query(Supplier).order_by(Supplier.name).offset(skip).limit(limit).all()
    def add(self, supplier: Supplier): self.db.add(supplier); self.db.flush(); return supplier
