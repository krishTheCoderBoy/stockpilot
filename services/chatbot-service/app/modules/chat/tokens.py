"""Signed, short-lived confirmation tokens for mutating actions.

A token binds the exact endpoint, body and user. It is signed (HMAC-SHA256) with a key
that is not the JWT secret, so the browser cannot edit the action, and a token minted for
one user is useless to another. Single use is enforced separately, in Redis.
"""
import base64
import hashlib
import hmac
import json
import re
import time
import uuid
from typing import Any

from app.core.config import settings

TOKEN_VERSION = 1

# Defence in depth: even a correctly signed token may only name these business endpoints,
# i.e. the same ones the UI itself uses. Anything else is refused at confirm time.
ALLOWED_ACTIONS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("POST", re.compile(r"^/purchase-orders/[0-9a-fA-F-]{36}/(submit|approve|mark-ordered|cancel|close|receive)$")),
    ("POST", re.compile(r"^/inventory-movements/$")),
    ("POST", re.compile(r"^/planning/recommendations/[0-9a-fA-F-]{36}/draft-po$")),
)


class ActionTokenError(Exception):
    """The token is malformed, forged, expired or not allowed. Message is user-safe."""


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _signature(body: str) -> str:
    return _b64(hmac.new(settings.action_signing_key, body.encode(), hashlib.sha256).digest())


def is_allowed_action(method: str, path: str) -> bool:
    return any(method == allowed_method and pattern.match(path) for allowed_method, pattern in ALLOWED_ACTIONS)


def issue_token(
    user_id: str, tool: str, summary: str, method: str, path: str, body: dict[str, Any] | None
) -> tuple[str, str, int]:
    """Returns (token, jti, expires_at_epoch)."""
    jti = uuid.uuid4().hex
    expires_at = int(time.time()) + settings.action_ttl_seconds
    payload = {"v": TOKEN_VERSION, "jti": jti, "sub": user_id, "tool": tool, "summary": summary[:300], "method": method, "path": path, "body": body, "exp": expires_at}
    encoded = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    return f"{encoded}.{_signature(encoded)}", jti, expires_at


def verify_token(token: str, user_id: str) -> dict[str, Any]:
    try:
        encoded, signature = token.split(".", 1)
    except ValueError as exc:
        raise ActionTokenError("This confirmation is not valid.") from exc
    if not hmac.compare_digest(signature, _signature(encoded)):
        raise ActionTokenError("This confirmation is not valid.")
    try:
        payload = json.loads(_unb64(encoded))
    except Exception as exc:
        raise ActionTokenError("This confirmation is not valid.") from exc
    if payload.get("v") != TOKEN_VERSION:
        raise ActionTokenError("This confirmation is not valid.")
    if payload.get("exp", 0) < time.time():
        raise ActionTokenError("This confirmation has expired. Ask the assistant to prepare the action again.")
    if payload.get("sub") != user_id:
        # Same message as a forged token: do not reveal that the token exists.
        raise ActionTokenError("This confirmation is not valid.")
    if not is_allowed_action(payload.get("method", ""), payload.get("path", "")):
        raise ActionTokenError("This action is not permitted.")
    return payload
