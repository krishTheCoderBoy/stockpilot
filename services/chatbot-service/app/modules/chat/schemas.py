from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, max_length=64)


class ToolCallInfo(BaseModel):
    name: str
    # Friendly text for the UI chip, e.g. "Checked stock levels".
    label: str
    status: Literal["ok", "error", "pending"]
    # Short plain-language failure reason, so the user can see why a lookup came up empty.
    error: str | None = None


class PendingActionOut(BaseModel):
    token: str
    tool: str
    summary: str
    details: dict[str, str]
    expires_at: datetime


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCallInfo]
    pending_action: PendingActionOut | None = None
    conversation_id: str


class ConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=4000)


class ConfirmResponse(BaseModel):
    status: Literal["success", "error"]
    http_status: int
    message: str
    result: dict[str, Any] | None = None
    # True when this is the stored outcome of an earlier confirmation of the same action.
    already_confirmed: bool = False
