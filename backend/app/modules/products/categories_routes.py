import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.users.models import UserRole
from app.modules.products.categories_models import ProductCategory
from app.modules.products.categories_repository import CategoryRepository
from app.modules.products.schemas import CategoryCreate, CategoryOut

router = APIRouter(prefix="/product-categories", tags=["product-categories"])


@router.post("/", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
):
    repo = CategoryRepository(db)
    category = ProductCategory(**payload.model_dump())
    return repo.create(category)


@router.get("/", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)
    ),
):
    repo = CategoryRepository(db)
    return repo.list_all()