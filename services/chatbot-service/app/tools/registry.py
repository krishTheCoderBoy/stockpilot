"""Tool registry: builds the API tool schemas and runs one tool call safely."""
import logging
import time
from dataclasses import dataclass, replace
from typing import Any

from pydantic import ValidationError

from app.tools.api import ApiError
from app.tools.base import Tool, ToolContext, ToolError
from app.tools.mutation_tools import MUTATION_TOOLS
from app.tools.read_tools import READ_TOOLS
from app.tools.trim import render

logger = logging.getLogger(__name__)


def _inline_refs(node: Any, defs: dict[str, Any]) -> Any:
    """Resolve $ref/$defs and drop pydantic's cosmetic titles, so the schema is a single
    self-contained object."""
    if isinstance(node, dict):
        if "$ref" in node:
            return _inline_refs(defs[node["$ref"].split("/")[-1]], defs)
        return {key: _inline_refs(value, defs) for key, value in node.items() if key not in ("title", "$defs")}
    if isinstance(node, list):
        return [_inline_refs(item, defs) for item in node]
    return node


def _build(tool: Tool) -> Tool:
    raw = tool.input_model.model_json_schema()
    schema = _inline_refs(raw, raw.get("$defs", {}))
    return replace(tool, schema=schema)


TOOLS: dict[str, Tool] = {tool.name: _build(tool) for tool in [*READ_TOOLS, *MUTATION_TOOLS]}


def tool_params(include_mutations: bool = True) -> list[dict[str, Any]]:
    return [
        {"name": tool.name, "description": tool.description, "input_schema": tool.schema}
        for tool in TOOLS.values()
        if include_mutations or not tool.mutating
    ]


@dataclass(frozen=True)
class ToolRun:
    content: str
    is_error: bool
    latency_ms: int


async def run_tool(name: str, raw_input: dict[str, Any], ctx: ToolContext) -> ToolRun:
    """Validate, execute and shrink one tool call. Never raises: every failure becomes a
    plain message the model can relay honestly."""
    started = time.monotonic()
    tool = TOOLS.get(name)
    try:
        if tool is None:
            raise ToolError(f"There is no tool called '{name}'.")
        try:
            args = tool.input_model.model_validate(raw_input)
        except ValidationError as exc:
            problems = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
            raise ToolError(f"Invalid arguments: {problems}") from exc
        outcome = await tool.handler(ctx, args)
        content, is_error = render({"untrusted_data": outcome.data}), False
    except ToolError as exc:
        content, is_error = str(exc), True
    except ApiError as exc:
        content, is_error = exc.message, True
    except Exception:
        # A bug in a tool must not leak internals to the model or the user.
        logger.exception("Tool %s crashed", name)
        content, is_error = "That tool failed unexpectedly. Try a different approach or tell the user it is unavailable.", True

    latency_ms = int((time.monotonic() - started) * 1000)
    # Arguments only: no tokens or response bodies are ever logged.
    logger.info("tool=%s status=%s latency_ms=%d args=%s", name, "error" if is_error else "ok", latency_ms, str(raw_input)[:200])
    return ToolRun(content, is_error, latency_ms)
