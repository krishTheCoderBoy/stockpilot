from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
# The service root is two levels above this file, so its own .env is found no matter which
# directory the process (uvicorn, alembic, a script) was started from. Real environment
# variables still override the file.
SERVICE_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "postgresql+psycopg2://stockpilot_user:stockpilot_pass@localhost:5432/procurement_db"
    secret_key: str = "changeme_dev_secret"
    algorithm: str = "HS256"
    inventory_service_url: str = "http://localhost:8002"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    rabbitmq_url: str = ""
    # Lets inventory-service jobs, which have no user token, read PO counts. Empty means
    # the internal endpoint refuses every request.
    internal_service_token: str = ""
    # --- Planning (reorder recommendations and demand forecasting) ---
    planning_history_days: int = 180
    # Window for the rule-based average daily demand.
    planning_rule_window_days: int = 30
    # How often orders can be placed: demand has to be covered until the next order lands.
    planning_review_period_days: int = 7
    # Used when a product has no default supplier, or its supplier has no lead time.
    planning_default_lead_time_days: int = 7
    planning_backtest_holdout_days: int = 14
    # Inventory data is shared by every user, so it can be cached briefly across requests.
    planning_inventory_cache_seconds: int = 60
    planning_forecast_cache_seconds: int = 1800
    model_config = SettingsConfigDict(env_file=SERVICE_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")
    @property
    def redis_uri(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
settings = Settings()
