from sqlalchemy.orm import Session

from app.modules.users.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()
    def get_by_email_or_mobile(self, identifier: str) -> User | None:
        return (
            self.db.query(User)
            .filter((User.email == identifier) | (User.mobile_no == identifier))
            .first()
        )

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user