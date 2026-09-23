from app.core.database import SessionLocal
from app.jobs.email_jobs import send_email_job
from app.modules.dashboard.service import DashboardService
from app.modules.users.models import User, UserRole


def scan_and_notify_low_stock_and_pending_pos() -> None:
    """
    Scheduled job: scans for low-stock items and PENDING purchase orders,
    emails ADMIN and INVENTORY_MANAGER users if anything needs attention.
    Runs in its own process (via rq-scheduler), so it opens its own DB session.
    """
    db = SessionLocal()
    try:
        service = DashboardService(db)
        notifications = service.get_notifications()

        if not notifications:
            return

        recipients = (
            db.query(User)
            .filter(User.role.in_([UserRole.ADMIN, UserRole.INVENTORY_MANAGER]))
            .filter(User.is_active.is_(True))
            .all()
        )

        body_lines = [n["message"] for n in notifications]
        body = "StockPilot daily summary:\n\n" + "\n".join(f"- {line}" for line in body_lines)

        for user in recipients:
            send_email_job(
                to_email=user.email,
                subject=f"StockPilot: {len(notifications)} item(s) need attention",
                body=body,
            )
    finally:
        db.close()