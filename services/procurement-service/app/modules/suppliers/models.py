import uuid

from sqlalchemy import Column, Computed, String, Boolean, Text, Integer, Index
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID

from app.core.database import Base


# Must stay identical to the expression in migration 8e1439173f7e; Postgres owns the
# value, so SQLAlchemy never writes it.
SUPPLIER_SEARCH_EXPRESSION = (
    "setweight(to_tsvector('english', coalesce(name, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(code, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(contact_person, '')), 'B')"
)


class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        Index("idx_suppliers_search_vector", "search_vector", postgresql_using="gin"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    search_vector = Column(TSVECTOR, Computed(SUPPLIER_SEARCH_EXPRESSION, persisted=True))