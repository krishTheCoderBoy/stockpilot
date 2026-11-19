"""Thin HTTP client for StockPilot's public API, always called with the end user's token.

The chatbot has no rights of its own: every request carries the caller's Authorization
header through the gateway, so the real services enforce RBAC exactly as they do for the UI.
"""
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SERVICE_BY_PREFIX = {
    "products": "inventory service",
    "product-categories": "inventory service",
    "warehouses": "inventory service",
    "inventory": "inventory service",
    "inventory-movements": "inventory service",
    "stock-reservations": "inventory service",
    "dashboard": "inventory service",
    "suppliers": "procurement service",
    "purchase-orders": "procurement service",
    "planning": "procurement service",
}


class ApiError(Exception):
    """A non-2xx answer or a transport failure, carrying a message safe to show the model
    and the user. `status` is 0 for transport failures."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass(frozen=True)
class ApiResponse:
    status: int
    data: Any


def _service_for(path: str) -> str:
    return SERVICE_BY_PREFIX.get(path.lstrip("/").split("/", 1)[0], "service")


def _detail_text(response: httpx.Response) -> str:
    """The API's own `detail`, verbatim for business-rule errors."""
    try:
        detail = response.json().get("detail")
    except Exception:
        return ""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):  # FastAPI validation errors
        parts = [f"{'.'.join(str(p) for p in item.get('loc', [])[1:])}: {item.get('msg', 'invalid')}" for item in detail if isinstance(item, dict)]
        return "Invalid input: " + "; ".join(parts)
    return ""


class GatewayClient:
    def __init__(self, authorization: str, http: httpx.AsyncClient):
        self._authorization = authorization
        self._http = http

    async def request(
        self, method: str, path: str, *, params: dict[str, Any] | None = None, json: Any = None
    ) -> ApiResponse:
        service = _service_for(path)
        try:
            response = await self._http.request(
                method,
                f"{settings.gateway_url.rstrip('/')}{path}",
                params={k: v for k, v in (params or {}).items() if v is not None},
                json=json,
                headers={"Authorization": self._authorization},
                timeout=settings.tool_timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            logger.warning("Timeout calling %s %s", method, path)
            raise ApiError(0, f"The {service} did not respond in time.") from exc
        except httpx.HTTPError as exc:
            logger.warning("Transport error calling %s %s: %s", method, path, type(exc).__name__)
            raise ApiError(0, f"The {service} could not be reached.") from exc

        if response.is_success:
            return ApiResponse(response.status_code, response.json() if response.content else None)

        detail = _detail_text(response)
        if response.status_code == 401:
            raise ApiError(401, "Your session has expired. Please sign in again.")
        if response.status_code == 403:
            raise ApiError(403, "You do not have permission to do this with your current role.")
        if response.status_code == 404:
            raise ApiError(404, detail or "That record was not found.")
        if response.status_code == 429:
            raise ApiError(429, "Too many requests right now; try again shortly.")
        if response.status_code >= 500:
            raise ApiError(response.status_code, f"The {service} reported an internal error.")
        raise ApiError(response.status_code, detail or f"The request was rejected (HTTP {response.status_code}).")

    async def get(self, path: str, **params: Any) -> Any:
        return (await self.request("GET", path, params=params)).data
