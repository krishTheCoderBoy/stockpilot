"""Compatibility export backed by shared JWT verification."""
import sys
from pathlib import Path
services_root = str(Path(__file__).resolve().parents[3])
if services_root not in sys.path:
    sys.path.insert(0, services_root)
from shared.auth.dependencies import configure_auth, decode_access_token
from app.core.config import settings
configure_auth(settings.secret_key, settings.algorithm)
__all__ = ["decode_access_token"]
