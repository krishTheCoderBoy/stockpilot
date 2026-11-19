"""Service-to-service client for purchase-order data owned by procurement-service."""
import logging
from typing import TypedDict

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class PurchaseOrderSummary(TypedDict):
    pending_count: int
    awaiting_approval_count: int


def get_purchase_order_summary(authorization: str | None = None) -> PurchaseOrderSummary | None:
    """Pending purchase-order counts, or None when procurement cannot be reached.

    A request-driven caller passes its own Authorization header so procurement applies
    that user's role. Scheduled jobs have no user, so they pass nothing and use the
    internal endpoint with the shared token. None (not an exception) lets the dashboard
    and the jobs carry on without this one figure.
    """
    base = settings.procurement_service_url.rstrip("/")
    if authorization:
        url, headers = f"{base}/purchase-orders/summary", {"Authorization": authorization}
    else:
        url, headers = f"{base}/internal/purchase-orders/summary", {"X-Internal-Token": settings.internal_service_token}
    try:
        response = httpx.get(url, headers=headers, timeout=3.0)
        response.raise_for_status()
        data = response.json()
        return {
            "pending_count": int(data["pending_count"]),
            "awaiting_approval_count": int(data["awaiting_approval_count"]),
        }
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        logger.warning("Purchase-order summary from procurement-service unavailable: %s", exc)
        return None
