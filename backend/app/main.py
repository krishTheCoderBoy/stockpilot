from fastapi import FastAPI

from app.core.config import settings
from app.modules.users.routes import router as users_router


app = FastAPI(title=settings.app_name)
app.include_router(users_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}