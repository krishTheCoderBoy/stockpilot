from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.suppliers.models import Supplier
from app.modules.suppliers.repository import SupplierRepository
from app.modules.suppliers.schemas import SupplierCreate, SupplierUpdate


class SupplierService:
    def __init__(self, db: Session):
        self.repo = SupplierRepository(db)

    def create_supplier(self, payload: SupplierCreate) -> Supplier:
        if self.repo.get_by_code(payload.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier code already exists",
            )
        supplier = Supplier(**payload.model_dump())
        return self.repo.create(supplier)

    def get_supplier(self, supplier_id) -> Supplier:
        supplier = self.repo.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found"
            )
        return supplier

    def list_suppliers(self, skip: int = 0, limit: int = 50) -> list[Supplier]:
        return self.repo.list_all(skip, limit)

    def update_supplier(self, supplier_id, payload: SupplierUpdate) -> Supplier:
        supplier = self.get_supplier(supplier_id)
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(supplier, field, value)
        return self.repo.update(supplier)