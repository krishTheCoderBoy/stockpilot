import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    name: str
    parent_category_id: uuid.UUID | None = None


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    parent_category_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: str | None = None
    category_id: uuid.UUID | None = None
    unit_price: Decimal
    unit_of_measure: str = "unit"
    reorder_point: Decimal = Decimal("0")
    min_order_quantity: Decimal = Decimal("1")
    max_stock_level: Decimal | None = None
    default_supplier_id: uuid.UUID | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category_id: uuid.UUID | None = None
    unit_price: Decimal | None = None
    unit_of_measure: str | None = None
    reorder_point: Decimal | None = None
    min_order_quantity: Decimal | None = None
    max_stock_level: Decimal | None = None
    is_active: bool | None = None
    default_supplier_id: uuid.UUID | None = None


class ProductOut(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    description: str | None
    category_id: uuid.UUID | None
    unit_price: Decimal
    unit_of_measure: str
    reorder_point: Decimal
    min_order_quantity: Decimal
    max_stock_level: Decimal | None
    is_active: bool
    default_supplier_id: uuid.UUID | None
    
    model_config = ConfigDict(from_attributes=True)