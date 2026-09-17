from fastapi import FastAPI

from app.core.config import settings
from app.modules.users.routes import router as users_router
from app.modules.auth.routes import router as auth_router
from app.modules.products.routes import router as products_router
from app.modules.products.categories_routes import router as categories_router
from app.modules.warehouses.routes import router as warehouses_router


app = FastAPI(title=settings.app_name)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(warehouses_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}