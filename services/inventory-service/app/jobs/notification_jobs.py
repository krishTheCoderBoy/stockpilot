import logging

from app.core.auth_client import RecipientLookupError, get_notification_recipients
from app.core.database import SessionLocal
from app.jobs.email_jobs import send_email_job
from app.modules.dashboard.service import DashboardService
from app.modules.inventory_batches.service import BatchService
from app.modules.products.models import Product
from app.modules.warehouses.models import Warehouse

logger = logging.getLogger(__name__)


def _recipients_or_none() -> list[str] | None:
    # Scheduled jobs run again on the next tick, so skipping one run is the graceful
    # outcome when auth-service is unreachable.
    try:
        return get_notification_recipients()
    except RecipientLookupError:
        logger.warning("Skipping notification run: recipients unavailable")
        return None


def _send_to_all(recipients: list[str], subject: str, body: str) -> None:
    for email in recipients:
        try:
            send_email_job(to_email=email, subject=subject, body=body)
        except Exception:
            # One bad address or SMTP hiccup must not stop the remaining recipients.
            logger.exception("Could not send notification to %s", email)


def scan_and_notify_expiring_batches() -> None:
    db = SessionLocal()
    try:
        expiring = BatchService(db).list_expiring(days=7)
        if not expiring:
            return

        recipients = _recipients_or_none()
        if not recipients:
            return

        lines = []
        for batch in expiring:
            product = db.query(Product).filter(Product.id == batch.product_id).first()
            warehouse = db.query(Warehouse).filter(Warehouse.id == batch.warehouse_id).first()
            lines.append(
                f"{product.name if product else 'Unknown'} — {batch.remaining_quantity} units, "
                f"batch {batch.batch_number}, expires {batch.expiry_date} "
                f"({warehouse.name if warehouse else 'Unknown warehouse'})"
            )

        body = "The following batches are expiring within 7 days:\n\n" + "\n".join(f"- {line}" for line in lines)
        _send_to_all(recipients, f"StockPilot: {len(expiring)} batch(es) expiring soon", body)
    finally:
        db.close()


def scan_and_notify_low_stock_and_pending_pos() -> None:
    """
    Scheduled job: emails ADMIN and INVENTORY_MANAGER users when stock is low or purchase
    orders await approval. Runs in its own process (rq-scheduler), so it opens its own
    session. Having no user token, it reads PO counts through procurement's internal
    endpoint; if that is down the PO line is just left out.
    """
    db = SessionLocal()
    try:
        notifications = DashboardService(db).get_notifications()
        if not notifications:
            return

        recipients = _recipients_or_none()
        if not recipients:
            return

        body = "StockPilot daily summary:\n\n" + "\n".join(f"- {n['message']}" for n in notifications)
        _send_to_all(recipients, f"StockPilot: {len(notifications)} item(s) need attention", body)
    finally:
        db.close()
