from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "StockPilot"
    environment: str = "development"
    debug: bool = True
    database_url: str = "postgresql+psycopg2://stockpilot_user:stockpilot_pass@localhost:5432/stockpilot_db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    secret_key: str = "changeme_dev_secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


settings = Settings()