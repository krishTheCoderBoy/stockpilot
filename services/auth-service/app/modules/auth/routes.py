from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    Token,
    VerifyLoginOtpRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MessageResponse,
    ForgotUsernameRequest,
    GoogleLoginRequest,
)
from app.modules.auth.service import AuthService
from fastapi import Request
from app.core.limiter import limiter
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])



def _limit(prod_limit: str) -> str:
    return prod_limit if settings.environment == "production" else "1000/minute"


@router.post("/login", response_model=LoginResponse)
@limiter.limit(_limit("5/minute"))
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    result = service.authenticate(payload.email, payload.password)
    return LoginResponse(**result)


@router.post("/verify-login-otp", response_model=Token)
@limiter.limit(_limit("5/minute"))
def verify_login_otp(request: Request, payload: VerifyLoginOtpRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    token = service.verify_login_otp(payload.email, payload.otp_code)
    return Token(access_token=token)


@router.post("/resend-login-otp", response_model=MessageResponse)
@limiter.limit(_limit("3/minute"))
def resend_login_otp(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.resend_login_otp(payload.email)
    return MessageResponse(message="A new OTP has been sent to your email.")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(_limit("3/minute"))
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.forgot_password(payload.email)
    return MessageResponse(message="If that email is registered, an OTP has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit(_limit("5/minute"))
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    service.reset_password(payload.email, payload.otp_code, payload.new_password)
    return MessageResponse(message="Password reset successful.")