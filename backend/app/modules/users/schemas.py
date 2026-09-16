import uuid

from pydantic import BaseModel, EmailStr, ConfigDict

from app.modules.users.models import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)