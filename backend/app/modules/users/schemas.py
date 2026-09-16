import uuid

from pydantic import BaseModel, EmailStr, ConfigDict

from app.modules.users.models import UserRole


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    mobile_no: str
    address: str | None = None
    password: str
    full_name: str
    role: UserRole


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    mobile_no: str
    address: str | None
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)