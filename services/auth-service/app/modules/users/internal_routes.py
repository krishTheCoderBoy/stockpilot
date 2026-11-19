from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_internal_token
from app.modules.users.models import UserRole
from app.modules.users.schemas import RecipientOut
from app.modules.users.service import UserService

# Service-to-service only: other services must not read auth_db directly, so they ask here.
router = APIRouter(
    prefix="/internal/users",
    tags=["internal"],
    include_in_schema=False,
    dependencies=[Depends(require_internal_token)],
)


@router.get("/recipients", response_model=list[RecipientOut])
def list_recipients(
    roles: list[UserRole] = Query(...),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.list_notification_recipients(roles)
