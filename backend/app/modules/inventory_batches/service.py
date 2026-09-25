from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.modules.inventory_batches.repository import BatchRepository


class BatchService:
    def __init__(self, db: Session):
        self.repo = BatchRepository(db)

    def list_by_product(self, product_id):
        return self.repo.list_by_product(product_id)

    def list_expiring(self, days: int = 7):
        cutoff = date.today() + timedelta(days=days)
        return self.repo.list_expiring(cutoff)