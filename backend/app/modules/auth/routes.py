from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.schemas import ForgotPasswordRequest, LoginRequest, LoginResponse, MessageResponse, Token, VerifyLoginOtpRequest
from app.modules.auth.service import AuthService
from app.core.deps import get_current_user
from app.modules.users.models import User


router = APIRouter(prefix="/auth", tags=["auth"])


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

@router.post("/resend-login-otp", response_model=MessageResponse)
def resend_login_otp(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.resend_login_otp(payload.email)
    return MessageResponse(message="A new OTP has been sent to your email.")

