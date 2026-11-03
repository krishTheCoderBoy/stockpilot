from sqlalchemy.orm import Session

from app.modules.products.models import Product
from sqlalchemy import func, text

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id) -> Product | None:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_by_sku(self, sku: str) -> Product | None:
        return self.db.query(Product).filter(Product.sku == sku).first()

    def list_all(self, skip: int = 0, limit: int = 50) -> list[Product]:
        return self.db.query(Product).offset(skip).limit(limit).all()

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.db.commit()
        self.db.refresh(product)
        return product


    def search(self, query: str, limit: int = 20) -> list[Product]:
        ts_query = func.websearch_to_tsquery("english", query)
        return (
            self.db.query(Product)
            .filter(Product.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank(Product.search_vector, ts_query).desc())
            .limit(limit)
            .all()
        )