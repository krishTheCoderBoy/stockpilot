from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import verify_password, create_access_token
from app.modules.users.repository import UserRepository
from app.modules.otp.service import OtpService
from app.modules.otp.models import OtpPurpose
from app.core.security import hash_password
from app.core.email import send_email


OTP_VALIDITY_DAYS = 30


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def _needs_otp(self, user) -> bool:
        if user.otp_verified_at is None:
            return True
        cutoff = datetime.now(timezone.utc) - timedelta(days=OTP_VALIDITY_DAYS)
        return user.otp_verified_at < cutoff

    def authenticate(self, email: str, password: str) -> dict:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not verified. Please verify OTP sent to your email.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        if self._needs_otp(user):
            otp_service = OtpService(self.db)
            otp_service.generate_and_send(user.id, user.email, OtpPurpose.LOGIN)
            return {"otp_required": True, "access_token": None, "message": "OTP sent to your email"}

        token = create_access_token(subject=str(user.id), role=user.role.value)
        return {"otp_required": False, "access_token": token, "message": None}

    def verify_login_otp(self, email: str, otp_code: str) -> str:
        user = self.repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        otp_service = OtpService(self.db)
        is_valid = otp_service.verify(user.id, OtpPurpose.LOGIN, otp_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP"
            )

        user.otp_verified_at = datetime.now(timezone.utc)
        self.db.commit()

        return create_access_token(subject=str(user.id), role=user.role.value)
    
    def forgot_password(self, email: str) -> None:
        user = self.repo.get_by_email(email)
        if not user:
            # Do not reveal whether the email exists
            return
        otp_service = OtpService(self.db)
        otp_service.generate_and_send(user.id, user.email, OtpPurpose.PASSWORD_RESET)

    def reset_password(self, email: str, otp_code: str, new_password: str) -> None:
        user = self.repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request"
            )

        otp_service = OtpService(self.db)
        is_valid = otp_service.verify(user.id, OtpPurpose.PASSWORD_RESET, otp_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP"
            )

        user.hashed_password = hash_password(new_password)
        self.db.commit()
    def forgot_username(self, identifier: str) -> None:
        user = self.repo.get_by_email_or_mobile(identifier)
        if not user:
            # Do not reveal whether the identifier exists
            return
        send_email(
            to_email=user.email,
            subject="Your StockPilot username",
            body=f"Your username is: {user.username}",
        )