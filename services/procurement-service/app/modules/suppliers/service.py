from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.modules.suppliers.models import Supplier
from app.modules.suppliers.repository import SupplierRepository
from app.modules.suppliers.schemas import SupplierCreate, SupplierUpdate
class SupplierService:
    def __init__(self, db: Session): self.db, self.repo = db, SupplierRepository(db)
    def create_supplier(self, payload: SupplierCreate):
        if self.repo.get_by_code(payload.code): raise HTTPException(status_code=400, detail="Supplier code already exists")
        try:
            value = self.repo.add(Supplier(**payload.model_dump())); self.db.commit(); self.db.refresh(value); return value
        except Exception:
            self.db.rollback(); raise
    def get_supplier(self, supplier_id):
        supplier = self.repo.get_by_id(supplier_id)
        if not supplier: raise HTTPException(status_code=404, detail="Supplier not found")
        return supplier
    def list_suppliers(self, skip: int = 0, limit: int = 50): return self.repo.list_all(skip, limit)
    def update_supplier(self, supplier_id, payload: SupplierUpdate):
        supplier = self.get_supplier(supplier_id)
        for field, value in payload.model_dump(exclude_unset=True).items(): setattr(supplier, field, value)
        try:
            self.db.commit(); self.db.refresh(supplier); return supplier
        except Exception:
            self.db.rollback(); raise
