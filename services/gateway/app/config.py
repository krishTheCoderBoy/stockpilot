from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    auth_service_url: str = "http://localhost:8001"
    inventory_service_url: str = "http://localhost:8002"
    procurement_service_url: str = "http://localhost:8003"
    request_timeout_seconds: float = 30.0
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
settings=Settings()
