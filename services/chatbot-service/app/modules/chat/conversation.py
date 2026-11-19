"""Optional short conversation memory in Redis. Losing it only means the assistant forgets
earlier turns, so every failure is logged and swallowed."""
import json
import logging
import re
import uuid

from app.core.config import settings
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
MAX_STORED_CHARS = 4000


def normalize_conversation_id(candidate: str | None) -> str:
    """Accept a client-supplied id only if it has our shape; otherwise start a new one."""
    if candidate and _ID_PATTERN.match(candidate):
        return candidate
    return uuid.uuid4().hex


def _key(user_id: str, conversation_id: str) -> str:
    # The user id is part of the key, so one user can never read another's conversation
    # by guessing its id.
    return f"chat:conv:{user_id}:{conversation_id}"


async def load_history(user_id: str, conversation_id: str) -> list[dict[str, str]]:
    try:
        raw = await redis_client.get(_key(user_id, conversation_id))
        history = json.loads(raw) if raw else []
    except Exception:
        logger.warning("Could not load conversation history", exc_info=True)
        return []
    # The API requires the first message to be from the user.
    while history and history[0].get("role") != "user":
        history.pop(0)
    return history


async def save_history(user_id: str, conversation_id: str, history: list[dict[str, str]]) -> None:
    trimmed = [
        {"role": m["role"], "content": m["content"][:MAX_STORED_CHARS]}
        for m in history[-settings.history_messages:]
    ]
    try:
        await redis_client.set(_key(user_id, conversation_id), json.dumps(trimmed), ex=settings.conversation_ttl_seconds)
    except Exception:
        logger.warning("Could not save conversation history", exc_info=True)
