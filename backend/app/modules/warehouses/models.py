import enum
import uuid

from sqlalchemy import Column, String, Boolean, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class WarehouseType(str, enum.Enum):
    MAIN = "MAIN"
    REGIONAL = "REGIONAL"
    TRANSIT = "TRANSIT"


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    capacity = Column(Numeric(14, 2), nullable=True)
    warehouse_type = Column(
        SAEnum(WarehouseType, name="warehouse_type"), nullable=False, default=WarehouseType.MAIN
    )
    is_active = Column(Boolean, default=True, nullable=False)