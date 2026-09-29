"""HTTP reverse proxy routing StockPilot service prefixes to their owners."""
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
from app.config import settings
app=FastAPI(title="StockPilot API Gateway", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"],allow_credentials=True,allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],allow_headers=["Authorization","Content-Type","Accept"])
ROUTES={
    "auth":settings.auth_service_url, "users":settings.auth_service_url, "otp":settings.auth_service_url,
    "products":settings.inventory_service_url, "product-categories":settings.inventory_service_url,
    "warehouses":settings.inventory_service_url, "inventory":settings.inventory_service_url,
    "inventory-movements":settings.inventory_service_url, "inventory-batches":settings.inventory_service_url,
    "suppliers":settings.procurement_service_url, "purchase-orders":settings.procurement_service_url,
}
HOP_BY_HOP={"connection","keep-alive","proxy-authenticate","proxy-authorization","te","trailers","transfer-encoding","upgrade","host","content-length","content-encoding"}
@app.get("/health")
async def health(): return {"status":"ok","service":"gateway"}
@app.api_route("/{path:path}",methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"])
async def proxy(path: str, request: Request):
    prefix=path.partition("/")[0]
    upstream=ROUTES.get(prefix)
    if upstream is None: raise HTTPException(status_code=404,detail="No service is configured for this path")
    target=f"{upstream.rstrip('/')}/{path}"
    if request.url.query: target=f"{target}?{request.url.query}"
    headers={k:v for k,v in request.headers.items() if k.lower() not in HOP_BY_HOP}
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds,follow_redirects=False) as client:
            result=await client.request(request.method,target,headers=headers,content=await request.body())
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504,detail="Upstream service timed out") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502,detail="Upstream service is unavailable") from exc
    response_headers={k:v for k,v in result.headers.items() if k.lower() not in HOP_BY_HOP and k.lower()!="set-cookie"}
    return Response(content=result.content,status_code=result.status_code,headers=response_headers,media_type=result.headers.get("content-type"))
