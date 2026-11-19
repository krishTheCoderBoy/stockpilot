"""Compatibility exports backed by the shared service authentication package."""
import hmac
import sys
from pathlib import Path

from fastapi import Header, HTTPException
services_root = str(Path(__file__).resolve().parents[3])
if services_root not in sys.path:
    sys.path.insert(0, services_root)
from shared.auth.dependencies import CurrentUser, configure_auth, get_current_user, require_role
from app.core.config import settings
configure_auth(settings.secret_key, settings.algorithm)
__all__ = ["CurrentUser", "get_current_user", "require_role"]


def require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    """Guards service-to-service endpoints; the gateway never routes /internal, and an
    unset token fails closed rather than open."""
    expected = settings.internal_service_token
    if not expected or not x_internal_token or not hmac.compare_digest(x_internal_token, expected):
        raise HTTPException(status_code=403, detail="Internal endpoint")
