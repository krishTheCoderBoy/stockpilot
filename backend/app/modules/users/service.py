from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import hash_password
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register_user(self, payload: UserCreate) -> User:
        if self.repo.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user = User(
            username=payload.username,
            email=payload.email,
            mobile_no=payload.mobile_no,
            address=payload.address,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role,
        )
        return self.repo.create(user)
    