"""Service-to-service client for user data owned by auth-service."""
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

NOTIFY_ROLES: tuple[str, ...] = ("ADMIN", "INVENTORY_MANAGER")


class RecipientLookupError(Exception):
    """Raised so each caller can choose its own degradation: consumers retry, jobs skip."""


def get_notification_recipients(roles: tuple[str, ...] = NOTIFY_ROLES) -> list[str]:
    """Return active users' email addresses for the given roles."""
    try:
        response = httpx.get(
            f"{settings.auth_service_url.rstrip('/')}/internal/users/recipients",
            params=[("roles", role) for role in roles],
            headers={"X-Internal-Token": settings.internal_service_token},
            timeout=4.0,
        )
        response.raise_for_status()
        return [user["email"] for user in response.json()]
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        logger.warning("Recipient lookup from auth-service failed: %s", exc)
        raise RecipientLookupError(str(exc)) from exc
