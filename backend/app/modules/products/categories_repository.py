from sqlalchemy.orm import Session

from app.modules.products.categories_models import ProductCategory


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, category: ProductCategory) -> ProductCategory:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_all(self) -> list[ProductCategory]:
        return self.db.query(ProductCategory).all()

    def get_by_id(self, category_id) -> ProductCategory | None:
        return (
            self.db.query(ProductCategory)
            .filter(ProductCategory.id == category_id)
            .first()
        )