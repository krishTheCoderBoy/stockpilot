"""Compatibility exports backed by the shared service authentication package."""
import sys
from pathlib import Path
services_root = str(Path(__file__).resolve().parents[3])
if services_root not in sys.path:
    sys.path.insert(0, services_root)
from shared.auth.dependencies import CurrentUser, configure_auth, get_current_user, require_role
from app.core.config import settings
configure_auth(settings.secret_key, settings.algorithm)
__all__ = ["CurrentUser", "get_current_user", "require_role"]
