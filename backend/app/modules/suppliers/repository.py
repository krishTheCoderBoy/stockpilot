from sqlalchemy.orm import Session

from app.modules.suppliers.models import Supplier


class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, supplier_id) -> Supplier | None:
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()

    def get_by_code(self, code: str) -> Supplier | None:
        return self.db.query(Supplier).filter(Supplier.code == code).first()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Supplier]:
        return self.db.query(Supplier).offset(skip).limit(limit).all()

    def create(self, supplier: Supplier) -> Supplier:
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def update(self, supplier: Supplier) -> Supplier:
        self.db.commit()
        self.db.refresh(supplier)
        return supplier