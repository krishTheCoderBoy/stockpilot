from pydantic_settings import BaseSettings, SettingsConfigDict

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
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    @property
    def redis_uri(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
settings = Settings()
