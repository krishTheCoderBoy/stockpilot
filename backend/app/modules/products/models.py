import uuid

from sqlalchemy import Column, String, Numeric, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True
    )
    unit_price = Column(Numeric(12, 2), nullable=False)
    unit_of_measure = Column(String, nullable=False, default="unit")
    reorder_point = Column(Numeric(12, 2), nullable=False, default=0)
    min_order_quantity = Column(Numeric(12, 2), nullable=False, default=1)
    max_stock_level = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)