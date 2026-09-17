from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    otp_required: bool
    access_token: str | None = None
    token_type: str = "bearer"
    message: str | None = None


class VerifyLoginOtpRequest(BaseModel):
    email: str
    otp_code: str