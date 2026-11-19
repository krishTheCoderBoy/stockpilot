from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_internal_token
from app.modules.purchase_orders.schemas import PurchaseOrderSummary
from app.modules.purchase_orders.service import PurchaseOrderService

# Service-to-service only. Scheduled jobs in inventory-service run without a user token,
# so they authenticate with the shared internal token instead.
router = APIRouter(
    prefix="/internal/purchase-orders",
    tags=["internal"],
    include_in_schema=False,
    dependencies=[Depends(require_internal_token)],
)


@router.get("/summary", response_model=PurchaseOrderSummary)
def po_summary(db: Session = Depends(get_db)) -> PurchaseOrderSummary:
    service = PurchaseOrderService(db)
    return service.summary()
