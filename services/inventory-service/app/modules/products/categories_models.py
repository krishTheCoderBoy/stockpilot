import uuid

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    parent_category_id = Column(
        UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True
    )