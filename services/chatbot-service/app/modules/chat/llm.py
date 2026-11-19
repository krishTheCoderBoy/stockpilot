"""The only place that talks to a model provider.

Two kinds of provider sit behind one small interface:
  - Anthropic (Claude), through the official SDK;
  - any OpenAI-compatible chat API (Groq, xAI Grok, ...), through plain HTTP.

Every provider failure (no key, bad key, rate limit, timeout, outage) is turned into
`LlmUnavailable` carrying a friendly reply, so /chat degrades instead of returning a 500.
"""
import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

import anthropic
import httpx

from app.core.config import settings
from app.modules.chat.prompts import (
    DEGRADED_REPLY,
    NOT_CONFIGURED_REPLY,
    RATE_LIMITED_REPLY,
    SYSTEM_PROMPT,
    TOOL_TROUBLE_REPLY,
)

logger = logging.getLogger(__name__)


class LlmUnavailable(Exception):
    def __init__(self, reply: str, reason: str):
        super().__init__(reason)
        self.reply = reply
        self.reason = reason


@dataclass(frozen=True)
class ToolUse:
    id: str
    name: str
    input: dict[str, Any]


@dataclass(frozen=True)
class ToolResultMsg:
    tool_use_id: str
    content: str
    is_error: bool


@dataclass(frozen=True)
class LlmTurn:
    text: str
    tool_uses: list[ToolUse]
    stop: Literal["end", "tool_use", "max_tokens", "refusal"]
    # Whatever the provider needs to replay this assistant turn in the next request.
    native: Any = field(default=None, repr=False)


class LlmProvider(ABC):
    name: str
    # True for providers with a small token budget: the service then sends fewer tools.
    compact: bool = False

    @abstractmethod
    async def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], allow_tools: bool) -> LlmTurn: ...

    @abstractmethod
    def add_assistant_turn(self, messages: list[dict[str, Any]], turn: LlmTurn) -> None: ...

    @abstractmethod
    def add_tool_results(self, messages: list[dict[str, Any]], results: list[ToolResultMsg]) -> None: ...


# ----------------------------------------------------------------------------- Anthropic (Claude)

class AnthropicProvider(LlmProvider):
    name = "anthropic"

    def __init__(self, api_key: str):
        # The SDK already retries 429/5xx/connection errors twice with backoff.
        self._client = anthropic.AsyncAnthropic(api_key=api_key, timeout=settings.llm_timeout_seconds, max_retries=2)

    async def complete(self, messages, tools, allow_tools):
        params: dict[str, Any] = {
            "model": settings.llm_model or settings.chatbot_model,
            "max_tokens": settings.chatbot_max_tokens,
            # Identical on every request, so mark it cacheable: follow-up calls inside one
            # turn then read the system prompt from cache.
            "system": [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            "tools": tools,
            "messages": messages,
            "output_config": {"effort": settings.chatbot_effort},
        }
        if not allow_tools:
            # Tool budget spent: answer, but call nothing else. (Tools stay listed because
            # the history contains tool_use blocks.)
            params["tool_choice"] = {"type": "none"}
        try:
            response = await self._client.messages.create(**params)
        except anthropic.RateLimitError as exc:
            logger.warning("LLM rate limited: %s", exc.message)
            raise LlmUnavailable(RATE_LIMITED_REPLY, "rate limited") from exc
        except anthropic.AuthenticationError as exc:
            logger.error("LLM authentication failed; check ANTHROPIC_API_KEY")
            raise LlmUnavailable(NOT_CONFIGURED_REPLY, "authentication failed") from exc
        except anthropic.APITimeoutError as exc:
            logger.warning("LLM request timed out")
            raise LlmUnavailable(DEGRADED_REPLY, "timeout") from exc
        except anthropic.APIConnectionError as exc:
            logger.warning("LLM unreachable: %s", type(exc).__name__)
            raise LlmUnavailable(DEGRADED_REPLY, "connection error") from exc
        except anthropic.APIStatusError as exc:
            logger.error("LLM returned HTTP %s: %s", exc.status_code, exc.message)
            raise LlmUnavailable(DEGRADED_REPLY, f"http {exc.status_code}") from exc

        uses = [ToolUse(b.id, b.name, dict(b.input)) for b in response.content if b.type == "tool_use"]
        text = "".join(b.text for b in response.content if b.type == "text")
        stop = {"tool_use": "tool_use", "refusal": "refusal", "max_tokens": "max_tokens"}.get(response.stop_reason, "end")
        return LlmTurn(text=text, tool_uses=uses, stop=stop, native=response.content)

    def add_assistant_turn(self, messages, turn):
        # Thinking blocks and tool_use blocks go back exactly as received.
        messages.append({"role": "assistant", "content": turn.native})

    def add_tool_results(self, messages, results):
        messages.append({
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": r.tool_use_id, "content": r.content, "is_error": r.is_error}
                for r in results
            ],
        })


# ----------------------------------------------------------------------------- OpenAI-compatible (Groq, xAI, ...)

MAX_RATE_LIMIT_RETRIES = 2
MAX_RATE_LIMIT_WAIT_SECONDS = 20.0


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    """How long to wait before retrying a 429: the provider's hint if given, else a short backoff."""
    header = response.headers.get("retry-after")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    match = re.search(r"try again in ([\d.]+)s", response.text)
    if match:
        return float(match.group(1)) + 0.5
    return 3.0 * (attempt + 1)


class OpenAICompatibleProvider(LlmProvider):
    def __init__(self, name: str, base_url: str, api_key: str, model: str, compact: bool):
        self.name = name
        self.compact = compact
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._api_key = api_key
        self._model = model

    @staticmethod
    def _tool_defs(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
            for t in tools
        ]

    async def complete(self, messages, tools, allow_tools):
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
            "tools": self._tool_defs(tools),
            "tool_choice": "auto" if allow_tools else "none",
            # Small cap on purpose: replies are short, and free tiers meter output tokens.
            "max_tokens": min(settings.chatbot_max_tokens, 1024),
        }
        if self._model.startswith("openai/gpt-oss"):
            # These are reasoning models; low effort keeps answers fast and cheap.
            payload["reasoning_effort"] = settings.llm_reasoning_effort

        response = await self._post(payload)
        choice = response.json()["choices"][0]
        message = choice["message"]
        raw_calls = message.get("tool_calls") or []

        uses: list[ToolUse] = []
        native_calls: list[dict[str, str]] = []
        for call in raw_calls:
            arguments = call["function"].get("arguments") or "{}"
            try:
                parsed = json.loads(arguments)
                if not isinstance(parsed, dict):
                    raise ValueError("arguments are not an object")
            except ValueError:
                # Unusable arguments become a validation error the model is told about.
                parsed = {"_unparseable_arguments": arguments[:200]}
            uses.append(ToolUse(call["id"], call["function"]["name"], parsed))
            native_calls.append({"id": call["id"], "name": call["function"]["name"], "arguments": arguments})

        finish = choice.get("finish_reason")
        if uses:
            stop = "tool_use"
        elif finish == "length":
            stop = "max_tokens"
        elif finish == "content_filter":
            stop = "refusal"
        else:
            stop = "end"
        return LlmTurn(text=message.get("content") or "", tool_uses=uses, stop=stop, native=native_calls)

    async def _post(self, payload: dict[str, Any]) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as http:
            for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
                try:
                    response = await http.post(self._url, headers=headers, json=payload)
                except httpx.TimeoutException as exc:
                    logger.warning("LLM request timed out")
                    raise LlmUnavailable(DEGRADED_REPLY, "timeout") from exc
                except httpx.HTTPError as exc:
                    logger.warning("LLM unreachable: %s", type(exc).__name__)
                    raise LlmUnavailable(DEGRADED_REPLY, "connection error") from exc

                if response.status_code == 429 and attempt < MAX_RATE_LIMIT_RETRIES:
                    delay = _retry_delay(response, attempt)
                    if delay <= MAX_RATE_LIMIT_WAIT_SECONDS:
                        # Free tiers meter tokens per minute; waiting briefly is usually enough.
                        logger.info("LLM rate limited; retrying in %.1fs", delay)
                        await asyncio.sleep(delay)
                        continue
                break

        if response.is_success:
            return response
        self._raise_for_status(response)
        raise AssertionError("unreachable")

    def _raise_for_status(self, response: httpx.Response) -> None:
        code, body = response.status_code, response.text
        if code in (401, 403):
            logger.error("LLM rejected the API key (HTTP %s); check GROK_API_KEY / LLM_API_KEY", code)
            raise LlmUnavailable(NOT_CONFIGURED_REPLY, "authentication failed")
        if code == 429:
            logger.warning("LLM rate limited after retries")
            raise LlmUnavailable(RATE_LIMITED_REPLY, "rate limited")
        if code == 404:
            logger.error("LLM endpoint or model not found (model=%s); set LLM_MODEL", self._model)
            raise LlmUnavailable(DEGRADED_REPLY, "model not found")
        if code == 400 and ("tool_use_failed" in body or "failed_generation" in body):
            # The model produced a malformed tool call; a rephrased question usually works.
            logger.warning("LLM produced a malformed tool call")
            raise LlmUnavailable(TOOL_TROUBLE_REPLY, "malformed tool call")
        logger.error("LLM returned HTTP %s: %s", code, body[:300])
        raise LlmUnavailable(DEGRADED_REPLY, f"http {code}")

    def add_assistant_turn(self, messages, turn):
        messages.append({
            "role": "assistant",
            "content": turn.text,
            "tool_calls": [
                {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["arguments"]}}
                for c in turn.native
            ],
        })

    def add_tool_results(self, messages, results):
        for r in results:
            messages.append({
                "role": "tool",
                "tool_call_id": r.tool_use_id,
                "content": f"ERROR: {r.content}" if r.is_error else r.content,
            })


# ----------------------------------------------------------------------------- selection

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
XAI_BASE_URL = "https://api.x.ai/v1"


def _build_provider() -> LlmProvider | None:
    choice = (settings.llm_provider or "auto").strip().lower()
    generic_key = settings.llm_api_key or settings.grok_api_key

    if choice == "auto":
        if settings.anthropic_api_key:
            choice = "anthropic"
        elif generic_key:
            # The key's own prefix says who issued it; the key is only ever sent to that
            # provider's official endpoint.
            choice = "groq" if generic_key.startswith("gsk_") else "xai" if generic_key.startswith("xai-") else "openai_compatible"
        else:
            return None

    if choice == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key) if settings.anthropic_api_key else None
    if not generic_key:
        return None
    if choice == "groq":
        return OpenAICompatibleProvider("groq", settings.llm_base_url or GROQ_BASE_URL, generic_key, settings.llm_model or "openai/gpt-oss-120b", compact=True)
    if choice == "xai":
        return OpenAICompatibleProvider("xai", settings.llm_base_url or XAI_BASE_URL, generic_key, settings.llm_model or "grok-4", compact=False)
    if choice == "openai_compatible":
        if not (settings.llm_base_url and settings.llm_model):
            logger.error("LLM_PROVIDER=openai_compatible needs LLM_BASE_URL and LLM_MODEL")
            return None
        return OpenAICompatibleProvider("openai_compatible", settings.llm_base_url, generic_key, settings.llm_model, compact=True)
    logger.error("Unknown LLM_PROVIDER %r", settings.llm_provider)
    return None


class LlmClient:
    def __init__(self) -> None:
        self._provider: LlmProvider | None = None

    def get_provider(self) -> LlmProvider:
        if self._provider is None:
            self._provider = _build_provider()
        if self._provider is None:
            raise LlmUnavailable(NOT_CONFIGURED_REPLY, "no model API key configured")
        return self._provider

    def describe(self) -> str | None:
        """Provider name for /health, or None when nothing is configured."""
        try:
            return self.get_provider().name
        except LlmUnavailable:
            return None


llm_client = LlmClient()
