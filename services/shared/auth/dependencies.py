"""Shared local JWT verification and role dependencies for StockPilot services."""
import os
from dataclasses import dataclass
from typing import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
oauth2_scheme = HTTPBearer()
_secret_key = os.environ.get("SECRET_KEY", "changeme_dev_secret")
_algorithm = os.environ.get("ALGORITHM", "HS256")
def configure_auth(secret_key: str, algorithm: str = "HS256") -> None:
    """Set credentials from the importing service's validated settings."""
    global _secret_key, _algorithm
    _secret_key, _algorithm = secret_key, algorithm
@dataclass(frozen=True)
class CurrentUser:
    id: str
    role: str
def decode_access_token(token: str) -> dict:
    """Decode a locally verifiable access token using shared service settings."""
    return jwt.decode(token, _secret_key, algorithms=[_algorithm])
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> CurrentUser:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_access_token(credentials.credentials)
        user_id, role = payload.get("sub"), payload.get("role")
        if not isinstance(user_id, str) or not user_id or not isinstance(role, str) or not role:
            raise unauthorized
        return CurrentUser(id=user_id, role=role)
    except (JWTError, TypeError, ValueError):
        raise unauthorized
def require_role(*allowed_roles: str) -> Callable:
    """Build a FastAPI dependency that restricts access to explicit role strings."""
    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action")
        return current_user
    return role_checker
