"""Issuing and confirming mutating actions.

Guarantees:
  - nothing runs without an explicit POST /chat/confirm from the user;
  - a token works once (Redis GETDEL on a "pending" marker), and repeating the confirmation
    returns the stored outcome instead of running the action again;
  - Redis being down means NO confirmation, never an unchecked execution.
"""
import json
import logging
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.redis_client import redis_client
from app.modules.chat.schemas import ConfirmResponse, PendingActionOut
from app.modules.chat.tokens import ActionTokenError, issue_token, verify_token
from app.tools.api import ApiError, GatewayClient
from app.tools.base import PendingAction
from app.tools.trim import pick

logger = logging.getLogger(__name__)


def _pending_key(jti: str) -> str:
    return f"chat:action:pending:{jti}"


def _result_key(jti: str) -> str:
    return f"chat:action:result:{jti}"


async def issue_pending_action(user_id: str, pending: PendingAction) -> PendingActionOut | None:
    """Mint the confirmation token. None if it could not be made confirmable (Redis down)."""
    token, jti, expires_at = issue_token(user_id, pending.tool, pending.summary, pending.method, pending.path, pending.body)
    try:
        await redis_client.set(_pending_key(jti), user_id, ex=settings.action_ttl_seconds)
    except Exception:
        logger.error("Could not store pending action; confirmation unavailable", exc_info=True)
        return None
    return PendingActionOut(
        token=token,
        tool=pending.tool,
        summary=pending.summary,
        details=pending.details,
        expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc),
    )


async def confirm_action(user_id: str, authorization: str, token: str) -> ConfirmResponse:
    try:
        payload = verify_token(token, user_id)
    except ActionTokenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    jti = payload["jti"]

    try:
        stored = await redis_client.get(_result_key(jti))
        if stored:
            return ConfirmResponse(**{**json.loads(stored), "already_confirmed": True})
        owner = await redis_client.getdel(_pending_key(jti))
    except RedisError as exc:
        logger.error("Redis unavailable while confirming an action", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Actions cannot be confirmed right now (confirmation storage is unavailable). Nothing was changed.",
        ) from exc

    if owner is None or owner != user_id:
        raise HTTPException(
            status_code=409,
            detail="This action was already handled, or it has expired. Check the record before trying again.",
        )

    outcome = await _execute(authorization, payload)
    try:
        await redis_client.set(_result_key(jti), outcome.model_dump_json(), ex=settings.action_result_ttl_seconds)
    except Exception:
        logger.warning("Could not store the action outcome", exc_info=True)
    logger.info("action=%s status=%s http=%s", payload["tool"], outcome.status, outcome.http_status)
    return outcome


async def _execute(authorization: str, payload: dict) -> ConfirmResponse:
    """Call the real business endpoint with the user's own token and report its answer."""
    async with httpx.AsyncClient() as http:
        api = GatewayClient(authorization, http)
        try:
            response = await api.request(payload["method"], payload["path"], json=payload.get("body"))
        except ApiError as exc:
            # The API's own message, verbatim for business-rule errors.
            return ConfirmResponse(status="error", http_status=exc.status, message=exc.message)

    data = response.data if isinstance(response.data, dict) else None
    shaped = pick(data, ("id", "po_number", "status", "movement_type", "quantity", "expected_date")) if data else None
    return ConfirmResponse(status="success", http_status=response.status, message=f"Done: {payload['summary']}.", result=shaped)
