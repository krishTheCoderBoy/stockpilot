from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.users.models import UserRole
from app.modules.dashboard.schemas import DashboardSummary, TrendPoint, RecentMovementOut
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.schemas import NotificationOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

READ_ROLES = (UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PROCUREMENT_MANAGER)


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), current_user=Depends(require_role(*READ_ROLES))):
    service = DashboardService(db)
    return service.get_summary()


@router.get("/inventory-trend", response_model=list[TrendPoint])
def get_inventory_trend(
    months: int = 6,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*READ_ROLES)),
):
    service = DashboardService(db)
    return service.get_inventory_trend(months)


@router.get("/recent-movements", response_model=list[RecentMovementOut])
def get_recent_movements(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*READ_ROLES)),
):
    service = DashboardService(db)
    return service.get_recent_movements(limit)


@router.get("/notifications", response_model=list[NotificationOut])
def get_notifications(db: Session = Depends(get_db), current_user=Depends(require_role(*READ_ROLES))):
    service = DashboardService(db)
    return service.get_notifications()