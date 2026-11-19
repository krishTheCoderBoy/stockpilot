from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.products.categories_service import CategoryService
from app.modules.products.schemas import CategoryCreate, CategoryOut

router = APIRouter(prefix="/product-categories", tags=["product-categories"])


@router.post("/", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN", "INVENTORY_MANAGER")),
):
    service = CategoryService(db)
    return service.create_category(payload)


@router.get("/", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN", "INVENTORY_MANAGER", "PROCUREMENT_MANAGER")),
):
    service = CategoryService(db)
    return service.list_categories()
