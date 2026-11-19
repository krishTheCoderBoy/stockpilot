import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import send_email
from app.modules.otp.models import Otp, OtpPurpose
from app.modules.otp.repository import OtpRepository
from app.jobs.email_jobs import send_email_job
from app.core.queue import email_queue

class OtpService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OtpRepository(db)

    def generate_and_send(self, user_id, email: str, purpose: OtpPurpose) -> None:
        code = f"{random.randint(0, 999999):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.otp_expiry_minutes
        )
        try:
            self.repo.invalidate_existing(user_id, purpose)
            self.repo.create(Otp(user_id=user_id, code=code, purpose=purpose, expires_at=expires_at))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        # Enqueued only after the commit, so a code is never emailed that the database
        # does not hold.
        email_queue.enqueue(
            send_email_job,
            to_email=email,
            subject="Your StockPilot verification code",
            body=f"Your OTP is {code}. It expires in {settings.otp_expiry_minutes} minutes.",
        )

        
    def verify(self, user_id, purpose: OtpPurpose, code: str) -> bool:
        """Marks the code used but does not commit: the caller commits it together with
        the change the code authorises (login time, password, verified flag), so a failure
        in between does not burn the code."""
        otp = self.repo.get_valid_otp(user_id, purpose, code)
        if not otp:
            return False
        self.repo.mark_used(otp)
        return True