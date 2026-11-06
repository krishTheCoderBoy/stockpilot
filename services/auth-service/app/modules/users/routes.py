from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import Request
from app.core.limiter import limiter

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.modules.users.models import User, UserRole
from app.modules.users.schemas import UserCreate, UserOut, VerifyOtpRequest
from app.modules.users.service import UserService
from app.core.config import settings
from app.core.limiter import limiter

router = APIRouter(prefix="/users", tags=["users"])

def _limit(prod_limit: str) -> str:
    return prod_limit if settings.environment == "production" else "1000/minute"

@router.post("/", response_model=UserOut, status_code=201)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    service = UserService(db)
    return service.register_user(payload)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/verify-otp", response_model=UserOut)
@limiter.limit(_limit("5/minute"))
def verify_registration_otp(request: Request, payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.verify_registration_otp(payload.email, payload.otp_code)