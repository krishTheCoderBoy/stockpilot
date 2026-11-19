from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
# Resolved from this file, not the working directory, so the gateway's own .env always loads.
SERVICE_ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    auth_service_url: str = "http://localhost:8001"
    inventory_service_url: str = "http://localhost:8002"
    procurement_service_url: str = "http://localhost:8003"
    chatbot_service_url: str = "http://localhost:8004"
    request_timeout_seconds: float = 30.0
    model_config = SettingsConfigDict(env_file=SERVICE_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")
settings=Settings()
