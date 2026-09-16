import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import send_email
from app.modules.otp.models import Otp, OtpPurpose
from app.modules.otp.repository import OtpRepository


class OtpService:
    def __init__(self, db: Session):
        self.repo = OtpRepository(db)

    def generate_and_send(self, user_id, email: str, purpose: OtpPurpose) -> None:
        self.repo.invalidate_existing(user_id, purpose)

        code = f"{random.randint(0, 999999):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.otp_expiry_minutes
        )
        otp = Otp(user_id=user_id, code=code, purpose=purpose, expires_at=expires_at)
        self.repo.create(otp)

        send_email(
            to_email=email,
            subject="Your StockPilot verification code",
            body=f"Your OTP is {code}. It expires in {settings.otp_expiry_minutes} minutes.",
        )

    def verify(self, user_id, purpose: OtpPurpose, code: str) -> bool:
        otp = self.repo.get_valid_otp(user_id, purpose, code)
        if not otp:
            return False
        self.repo.mark_used(otp)
        return True