"""Shrink API data before it goes back to the model: fewer tokens, less untrusted text."""
import json
from typing import Any

from app.core.config import settings

MAX_STRING_CHARS = 240
MAX_LIST_ITEMS = 25


def pick(row: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """Only the listed fields, so unrelated columns never reach the model."""
    return {key: row[key] for key in keys if key in row}


def shorten(value: Any) -> Any:
    if isinstance(value, str):
        return value if len(value) <= MAX_STRING_CHARS else value[:MAX_STRING_CHARS] + "…"
    if isinstance(value, list):
        trimmed = [shorten(item) for item in value[:MAX_LIST_ITEMS]]
        if len(value) > MAX_LIST_ITEMS:
            trimmed.append(f"… {len(value) - MAX_LIST_ITEMS} more not shown")
        return trimmed
    if isinstance(value, dict):
        return {key: shorten(item) for key, item in value.items()}
    return value


def render(data: Any) -> str:
    """Serialize tool data for the model, with a hard size cap."""
    text = json.dumps(shorten(data), default=str, ensure_ascii=False)
    if len(text) > settings.tool_result_max_chars:
        text = text[: settings.tool_result_max_chars] + '… [result truncated; ask for a narrower query]'
    return text
