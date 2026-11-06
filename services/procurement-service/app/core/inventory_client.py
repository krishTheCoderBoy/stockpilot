import httpx
from fastapi import HTTPException
from app.core.config import settings
def validate_inventory_resource(path: str, resource_id: str, authorization: str) -> None:
    try:
        response = httpx.get(f"{settings.inventory_service_url}/{path}/{resource_id}", headers={"Authorization": authorization}, timeout=4.0)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Inventory service is unavailable") from exc
    if response.status_code == 404:
        raise HTTPException(status_code=400, detail=f"Unknown {path[:-1]} {resource_id}")
    if response.is_error:
        raise HTTPException(status_code=503, detail="Inventory service could not validate the resource")
