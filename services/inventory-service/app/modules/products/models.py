import uuid

from sqlalchemy import Column, Computed, String, Numeric, Boolean, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.core.database import Base


# Must stay identical to the expression in migration 832942e4a3ce; Postgres owns the
# value, so SQLAlchemy never writes it.
PRODUCT_SEARCH_EXPRESSION = (
    "setweight(to_tsvector('english', coalesce(name, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(sku, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(description, '')), 'B')"
)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("idx_products_search_vector", "search_vector", postgresql_using="gin"),
    )

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
    # Supplier is owned by procurement; this UUID is validated through its service API.
    default_supplier_id = Column(UUID(as_uuid=True), nullable=True)
    search_vector = Column(TSVECTOR, Computed(PRODUCT_SEARCH_EXPRESSION, persisted=True))