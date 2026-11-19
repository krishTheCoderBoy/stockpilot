import enum
import uuid

from sqlalchemy import Column, Computed, String, Boolean, Numeric, Index, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.core.database import Base


class WarehouseType(str, enum.Enum):
    MAIN = "MAIN"
    REGIONAL = "REGIONAL"
    TRANSIT = "TRANSIT"


# Must stay identical to the expression in migration 7d896323cfb5; Postgres owns the
# value, so SQLAlchemy never writes it.
WAREHOUSE_SEARCH_EXPRESSION = (
    "setweight(to_tsvector('english', coalesce(name, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(code, '')), 'A') || "
    "setweight(to_tsvector('english', coalesce(city, '')), 'B') || "
    "setweight(to_tsvector('english', coalesce(state, '')), 'B')"
)


class Warehouse(Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        Index("idx_warehouses_search_vector", "search_vector", postgresql_using="gin"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    # User records live in auth_db, so the manager ID is trusted as an external UUID.
    manager_id = Column(UUID(as_uuid=True), nullable=True)
    capacity = Column(Numeric(14, 2), nullable=True)
    warehouse_type = Column(
        SAEnum(WarehouseType, name="warehouse_type"), nullable=False, default=WarehouseType.MAIN
    )
    is_active = Column(Boolean, default=True, nullable=False)
    search_vector = Column(TSVECTOR, Computed(WAREHOUSE_SEARCH_EXPRESSION, persisted=True))
