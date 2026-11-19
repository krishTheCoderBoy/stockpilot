"""Tool framework: a tool is a pydantic input model plus one small async handler."""
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from pydantic import BaseModel

from app.tools.api import GatewayClient


class ToolError(Exception):
    """A failure the model should be told about in plain words (permission, not found,
    service down, bad arguments). Never a stack trace and never a secret."""


@dataclass(frozen=True)
class PendingAction:
    """A mutation prepared but NOT executed. The user has to confirm it from the UI."""
    tool: str
    summary: str
    details: dict[str, str]
    method: str
    path: str
    body: dict[str, Any] | None


@dataclass
class ToolContext:
    api: GatewayClient
    user_id: str
    role: str
    # Filled by mutation tools; at most one action may await confirmation per turn.
    pending: PendingAction | None = None


@dataclass(frozen=True)
class ToolOutcome:
    """What the model sees. `data` is untrusted business data (it may contain free text a
    user typed into a product description or PO note) and is presented as such."""
    data: Any


Handler = Callable[[ToolContext, BaseModel], Awaitable[ToolOutcome]]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_model: type[BaseModel]
    handler: Handler
    # Shown to the user as a chip, e.g. "Checked stock levels".
    label: str
    mutating: bool = False
    # Filled in by the registry.
    schema: dict[str, Any] = field(default_factory=dict)


def parse_uuid(value: str, what: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise ToolError(f"'{value}' is not a valid {what} id. Look it up with the search tool first.") from exc
