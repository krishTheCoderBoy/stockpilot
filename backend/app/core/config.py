from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    app_name: str = "StockPilot"
    environment: str = "development"
    debug: bool = True
    database_url: str = "postgresql+psycopg2://stockpilot_user:stockpilot_pass@localhost:5432/stockpilot_db"
    test_database_url: str = "postgresql+psycopg2://stockpilot_user:choose_a_strong_password@localhost:5432/stockpilot_test_db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    secret_key: str = "changeme_dev_secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@stockpilot.com"
    otp_expiry_minutes: int = 10
    google_client_id: str = ""
    redis_host: str = ""
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    @model_validator(mode="after")
    def check_secret_key(self):
        if self.environment == "production" and self.secret_key == "changeme_dev_secret":
            raise ValueError("SECRET_KEY must be set to a real value in production")
        return self
    
    @property
    def redis_uri(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

settings = Settings()