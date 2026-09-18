from fastapi import FastAPI

from app.core.config import settings
from app.modules.users.routes import router as users_router
from app.modules.auth.routes import router as auth_router
from app.modules.products.routes import router as products_router
from app.modules.products.categories_routes import router as categories_router
from app.modules.warehouses.routes import router as warehouses_router
from app.modules.inventory.routes import router as inventory_router
from app.modules.inventory_movements.routes import router as movements_router
from app.modules.suppliers.routes import router as suppliers_router
from app.modules.purchase_orders.routes import router as po_router


app = FastAPI(title=settings.app_name)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(po_router)
app.include_router(suppliers_router)
app.include_router(inventory_router)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(warehouses_router)
app.include_router(movements_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}