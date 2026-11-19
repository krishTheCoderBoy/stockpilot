import asyncio
import logging
import re
from typing import Any

import httpx

from app.core.config import settings
from app.core.deps import CurrentUser
from app.modules.chat import conversation
from app.modules.chat.actions import confirm_action, issue_pending_action
from app.modules.chat.formatting import to_plain_text
from app.modules.chat.llm import LlmClient, LlmProvider, LlmUnavailable, ToolResultMsg, ToolUse, llm_client
from app.modules.chat.prompts import REFUSAL_REPLY
from app.modules.chat.schemas import ChatRequest, ChatResponse, ConfirmResponse, ToolCallInfo
from app.tools.api import GatewayClient
from app.tools.base import ToolContext
from app.tools.registry import TOOLS, ToolRun, run_tool, tool_params

logger = logging.getLogger(__name__)

TOOL_LIMIT_MESSAGE = "Tool call limit reached for this turn. Answer with what you already have, and say what is missing."
STEP_LIMIT_REPLY = "That needed more steps than I am allowed to take in one message. Could you narrow the question?"
CONFIRM_UNAVAILABLE_NOTE = (
    "\n\nI could not prepare the confirmation step just now (temporary storage problem), "
    "so nothing has been changed. Please try again in a moment."
)

# On providers with a small token budget the action tools (about half the tool definitions)
# are only offered when a recent user message sounds like a request to change something.
ACTION_HINT = re.compile(
    r"\b(receiv\w*|submit\w*|approv\w*|cancel\w*|mark\w*|record\w*|issu(?:e|ed|ing)|damag\w*|return\w*|"
    r"adjust\w*|creat\w*|draft\w*|confirm\w*|reserv\w*|write[- ]?off|go ahead|do it)\b",
    re.IGNORECASE,
)


def _recent_user_text(messages: list[dict[str, Any]], count: int = 3) -> str:
    texts = [m["content"] for m in messages if m.get("role") == "user" and isinstance(m.get("content"), str)]
    return " ".join(texts[-count:])


def _tools_for(provider: LlmProvider, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if provider.compact and not ACTION_HINT.search(_recent_user_text(messages)):
        return tool_params(include_mutations=False)
    return tool_params()


class ChatService:
    def __init__(self, llm: LlmClient = llm_client):
        self.llm = llm

    async def handle(self, user: CurrentUser, authorization: str, request: ChatRequest) -> ChatResponse:
        conversation_id = conversation.normalize_conversation_id(request.conversation_id)
        history = await conversation.load_history(user.id, conversation_id)
        messages: list[dict[str, Any]] = [*history, {"role": "user", "content": request.message}]
        calls: list[ToolCallInfo] = []

        async with httpx.AsyncClient() as http:
            ctx = ToolContext(api=GatewayClient(authorization, http), user_id=user.id, role=user.role)
            try:
                reply = await self._run_model_loop(messages, ctx, calls)
            except LlmUnavailable as exc:
                logger.warning("Chat degraded: %s", exc.reason)
                return ChatResponse(reply=exc.reply, tool_calls=calls, pending_action=None, conversation_id=conversation_id)

        pending_out = None
        if ctx.pending is not None:
            pending_out = await issue_pending_action(user.id, ctx.pending)
            if pending_out is None:
                reply += CONFIRM_UNAVAILABLE_NOTE
                calls = [c.model_copy(update={"status": "error"}) if c.status == "pending" else c for c in calls]

        stored_reply = reply
        if pending_out is not None:
            stored_reply += f"\n[Awaiting the user's confirmation: {pending_out.summary}]"
        await conversation.save_history(
            user.id,
            conversation_id,
            [*history, {"role": "user", "content": request.message}, {"role": "assistant", "content": stored_reply}],
        )
        return ChatResponse(reply=reply, tool_calls=calls, pending_action=pending_out, conversation_id=conversation_id)

    async def confirm(self, user: CurrentUser, authorization: str, token: str) -> ConfirmResponse:
        return await confirm_action(user.id, authorization, token)

    async def _run_model_loop(self, messages: list[dict[str, Any]], ctx: ToolContext, calls: list[ToolCallInfo]) -> str:
        provider = self.llm.get_provider()
        tool_budget = settings.max_tool_calls_per_turn
        tools = _tools_for(provider, messages)

        for _ in range(settings.max_model_calls_per_turn):
            turn = await provider.complete(messages, tools, allow_tools=tool_budget > 0)

            if turn.stop == "tool_use":
                provider.add_assistant_turn(messages, turn)
                results, tool_budget = await self._run_tools(turn.tool_uses, ctx, calls, tool_budget)
                provider.add_tool_results(messages, results)
                continue

            if turn.stop == "refusal":
                return REFUSAL_REPLY
            text = to_plain_text(turn.text)
            if turn.stop == "max_tokens":
                text += "\n\n(My answer was cut short; ask me to continue if you need more.)"
            if not text:
                text = "I've prepared that for you below." if ctx.pending else "I wasn't able to put together an answer. Could you rephrase?"
            return text

        return STEP_LIMIT_REPLY

    async def _run_tools(
        self, uses: list[ToolUse], ctx: ToolContext, calls: list[ToolCallInfo], budget: int
    ) -> tuple[list[ToolResultMsg], int]:
        """Run this round's tool calls. Reads run concurrently; mutations (which only prepare
        a confirmation) run one at a time afterwards."""
        allowed = uses[: max(budget, 0)]
        skipped = uses[max(budget, 0):]

        reads = [u for u in allowed if not (TOOLS.get(u.name) and TOOLS[u.name].mutating)]
        writes = [u for u in allowed if u not in reads]
        runs: dict[str, ToolRun] = dict(
            zip([u.id for u in reads], await asyncio.gather(*[run_tool(u.name, u.input, ctx) for u in reads]))
        )
        for use in writes:
            runs[use.id] = await run_tool(use.name, use.input, ctx)

        results: list[ToolResultMsg] = []
        for use in allowed:
            run = runs[use.id]
            tool = TOOLS.get(use.name)
            prepared = bool(tool and tool.mutating and not run.is_error)
            calls.append(ToolCallInfo(
                name=use.name,
                label=tool.label if tool else use.name,
                status="pending" if prepared else ("error" if run.is_error else "ok"),
                error=run.content[:200] if run.is_error else None,
            ))
            results.append(ToolResultMsg(use.id, run.content, run.is_error))
        for use in skipped:
            results.append(ToolResultMsg(use.id, TOOL_LIMIT_MESSAGE, True))
        return results, budget - len(allowed)
