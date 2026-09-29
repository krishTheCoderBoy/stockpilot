import uuid

from pydantic import BaseModel, EmailStr, ConfigDict


class SupplierCreate(BaseModel):
    code: str
    name: str
    contact_person: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    lead_time_days: int | None = None


class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_person: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    lead_time_days: int | None = None
    is_active: bool | None = None


class SupplierOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    contact_person: str | None
    email: str | None
    phone: str | None
    address: str | None
    lead_time_days: int | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)