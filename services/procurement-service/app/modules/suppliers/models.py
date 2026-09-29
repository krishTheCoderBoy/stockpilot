import uuid

from sqlalchemy import Column, String, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    contact_person = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)