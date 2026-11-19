from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.products.categories_models import ProductCategory
from app.modules.products.categories_repository import CategoryRepository
from app.modules.products.schemas import CategoryCreate


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)

    def create_category(self, payload: CategoryCreate) -> ProductCategory:
        if self.repo.get_by_name(payload.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists"
            )
        if payload.parent_category_id and not self.repo.get_by_id(payload.parent_category_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Parent category not found"
            )
        try:
            category = self.repo.create(ProductCategory(**payload.model_dump()))
            self.db.commit()
            self.db.refresh(category)
            return category
        except Exception:
            self.db.rollback()
            raise

    def list_categories(self) -> list[ProductCategory]:
        return self.repo.list_all()
