from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.otp.models import Otp, OtpPurpose


class OtpRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, otp: Otp) -> Otp:
        self.db.add(otp)
        self.db.commit()
        self.db.refresh(otp)
        return otp

    def get_valid_otp(self, user_id, purpose: OtpPurpose, code: str) -> Otp | None:
        return (
            self.db.query(Otp)
            .filter(
                Otp.user_id == user_id,
                Otp.purpose == purpose,
                Otp.code == code,
                Otp.is_used.is_(False),
                Otp.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

    def mark_used(self, otp: Otp) -> None:
        otp.is_used = True
        self.db.commit()

    def invalidate_existing(self, user_id, purpose: OtpPurpose) -> None:
        self.db.query(Otp).filter(
            Otp.user_id == user_id,
            Otp.purpose == purpose,
            Otp.is_used.is_(False),
        ).update({"is_used": True})
        self.db.commit()