from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.schemas import LoginRequest, Token
from app.modules.auth.service import AuthService
from app.core.deps import get_current_user
from app.modules.users.models import User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    token = service.authenticate(payload.email, payload.password)
    return Token(access_token=token)

