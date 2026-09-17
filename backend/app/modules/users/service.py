from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import hash_password
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate
from app.modules.otp.service import OtpService
from app.modules.otp.models import OtpPurpose


class UserService:
    def __init__(self, db: Session):
        self.db = db
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
            is_verified=False,
        )
        user = self.repo.create(user)

        otp_service = OtpService(self.db)
        otp_service.generate_and_send(user.id, user.email, OtpPurpose.REGISTRATION)

        return user

    
    def verify_registration_otp(self, email: str, otp_code: str) -> User:
        user = self.repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified"
            )

        otp_service = OtpService(self.db)
        is_valid = otp_service.verify(user.id, OtpPurpose.REGISTRATION, otp_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP"
            )

        user.is_verified = True
        self.db.commit()
        self.db.refresh(user)
        return user