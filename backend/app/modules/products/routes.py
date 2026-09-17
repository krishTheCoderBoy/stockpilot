import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.users.models import UserRole
from app.modules.products.schemas import ProductCreate, ProductOut, ProductUpdate
from app.modules.products.service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
):
    service = ProductService(db)
    return service.create_product(payload)


@router.get("/", response_model=list[ProductOut])
def list_products(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)),
):
    service = ProductService(db)
    return service.list_products(skip, limit)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)),
):
    service = ProductService(db)
    return service.get_product(product_id)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
):
    service = ProductService(db)
    return service.update_product(product_id, payload)