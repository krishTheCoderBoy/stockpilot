import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, require_role
from app.modules.planning.rules import RiskLevel
from app.modules.planning.schemas import (
    DraftPurchaseOrderRequest,
    ForecastOut,
    PlanningSummary,
    RecommendationOut,
    RecommendationPage,
)
from app.modules.planning.service import PlanningService
from app.modules.purchase_orders.schemas import PurchaseOrderOut

router = APIRouter(prefix="/planning", tags=["planning"])

# Inventory managers can read plans but not turn them into orders.
READ_ROLES = ("ADMIN", "INVENTORY_MANAGER", "PROCUREMENT_MANAGER")
WRITE_ROLES = ("ADMIN", "PROCUREMENT_MANAGER")


@router.get("/recommendations", response_model=RecommendationPage)
def list_recommendations(
    risk: RiskLevel | None = None,
    supplier_id: uuid.UUID | None = None,
    warehouse_id: uuid.UUID | None = None,
    mode: Literal["auto", "rules"] = "auto",
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = PlanningService(db, authorization)
    return service.list_recommendations(risk, supplier_id, warehouse_id, mode, skip, limit)


@router.get("/summary", response_model=PlanningSummary)
def get_summary(
    warehouse_id: uuid.UUID | None = None,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = PlanningService(db, authorization)
    return service.summary(warehouse_id)


@router.get("/recommendations/{product_id}", response_model=RecommendationOut)
def get_recommendation(
    product_id: uuid.UUID,
    warehouse_id: uuid.UUID | None = None,
    mode: Literal["auto", "rules"] = "auto",
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = PlanningService(db, authorization)
    return service.get_recommendation(product_id, warehouse_id, mode)


@router.get("/forecast/{product_id}", response_model=ForecastOut)
def get_forecast(
    product_id: uuid.UUID,
    warehouse_id: uuid.UUID | None = None,
    horizon_days: int | None = Query(default=None, ge=1, le=90),
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*READ_ROLES)),
):
    service = PlanningService(db, authorization)
    return service.get_forecast(product_id, warehouse_id, horizon_days)


@router.post("/recommendations/{product_id}/draft-po", response_model=PurchaseOrderOut, status_code=201)
def create_draft_purchase_order(
    product_id: uuid.UUID,
    payload: DraftPurchaseOrderRequest,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(*WRITE_ROLES)),
):
    service = PlanningService(db, authorization)
    return service.create_draft_po(product_id, payload, current_user.id)
