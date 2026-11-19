from fastapi import APIRouter, Depends, Header, Request

from app.core.config import settings
from app.core.deps import CurrentUser, require_role
from app.core.limiter import limiter
from app.modules.chat.schemas import ChatRequest, ChatResponse, ConfirmRequest, ConfirmResponse
from app.modules.chat.service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

# Same roles that can read StockPilot data at all. What each user can actually do is decided
# by the business services the tools call with the user's own token.
ROLES = ("ADMIN", "INVENTORY_MANAGER", "PROCUREMENT_MANAGER")


def _limit(prod_limit: str) -> str:
    return prod_limit if settings.environment == "production" else "1000/minute"


@router.post("", response_model=ChatResponse)
@limiter.limit(_limit("10/minute"))
async def chat(
    request: Request,
    payload: ChatRequest,
    authorization: str = Header(default=""),
    current_user: CurrentUser = Depends(require_role(*ROLES)),
):
    service = ChatService()
    return await service.handle(current_user, authorization, payload)


@router.post("/confirm", response_model=ConfirmResponse)
@limiter.limit(_limit("20/minute"))
async def confirm(
    request: Request,
    payload: ConfirmRequest,
    authorization: str = Header(default=""),
    current_user: CurrentUser = Depends(require_role(*ROLES)),
):
    service = ChatService()
    return await service.confirm(current_user, authorization, payload.token)
