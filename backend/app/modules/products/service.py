from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.products.models import Product
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, db: Session):
        self.repo = ProductRepository(db)

    def create_product(self, payload: ProductCreate) -> Product:
        if self.repo.get_by_sku(payload.sku):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU already exists",
            )
        product = Product(**payload.model_dump())
        return self.repo.create(product)

    def get_product(self, product_id) -> Product:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )
        return product

    def list_products(self, skip: int = 0, limit: int = 50) -> list[Product]:
        return self.repo.list_all(skip, limit)

    def update_product(self, product_id, payload: ProductUpdate) -> Product:
        product = self.get_product(product_id)
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(product, field, value)
        return self.repo.update(product)