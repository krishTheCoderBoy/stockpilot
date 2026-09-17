from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.users.schemas import UserCreate, UserOut
from app.modules.users.service import UserService
from app.core.deps import get_current_user
from app.modules.users.models import User
from app.core.deps import require_role
from app.modules.users.models import UserRole
from app.modules.users.schemas import VerifyOtpRequest
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    Token,
    VerifyLoginOtpRequest,
)
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
)
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import ForgotUsernameRequest
from app.modules.auth.schemas import GoogleLoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut, status_code=201)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.register_user(payload)
@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
@router.post("/", response_model=UserOut, status_code=201)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.ADMIN)),
):
    service = UserService(db)
    return service.register_user(payload)

@router.post("/verify-otp", response_model=UserOut)
def verify_registration_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.verify_registration_otp(payload.email, payload.otp_code)
@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    result = service.authenticate(payload.email, payload.password)
    return LoginResponse(**result)


@router.post("/verify-login-otp", response_model=Token)
def verify_login_otp(payload: VerifyLoginOtpRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    token = service.verify_login_otp(payload.email, payload.otp_code)
    return Token(access_token=token)
@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.forgot_password(payload.email)
    return MessageResponse(message="If that email is registered, an OTP has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.reset_password(payload.email, payload.otp_code, payload.new_password)
    return MessageResponse(message="Password reset successful.")



@router.post("/forgot-username", response_model=MessageResponse)
def forgot_username(payload: ForgotUsernameRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.forgot_username(payload.identifier)
    return MessageResponse(message="If that identifier is registered, your username has been emailed.")




@router.post("/google", response_model=Token)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    token = service.google_login(payload.id_token)
    return Token(access_token=token)
