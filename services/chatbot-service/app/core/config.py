from pathlib import Path
import hashlib
import hmac

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The service root is two levels above this file, so its own .env is found no matter which
# directory the process (uvicorn, alembic, a script) was started from. Real environment
# variables still override the file.
SERVICE_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    environment: str = "development"
    secret_key: str = "changeme_dev_secret"
    algorithm: str = "HS256"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # Business APIs are reached through the gateway, exactly like the browser does.
    gateway_url: str = "http://localhost:8000"
    tool_timeout_seconds: float = 20.0

    # Which model answers. "auto" uses Anthropic when ANTHROPIC_API_KEY is set, otherwise the
    # Groq or xAI key in GROK_API_KEY (recognised by its prefix: gsk_ = Groq, xai- = xAI).
    # Explicit values: anthropic | groq | xai | openai_compatible.
    llm_provider: str = "auto"
    anthropic_api_key: str = ""
    grok_api_key: str = ""
    # Generic override key / endpoint / model for any OpenAI-compatible provider.
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    # Reasoning effort for gpt-oss style models: low | medium | high.
    llm_reasoning_effort: str = "low"
    chatbot_model: str = "claude-sonnet-5-5"
    chatbot_effort: str = "medium"
    chatbot_max_tokens: int = 2048
    llm_timeout_seconds: float = 60.0

    # Bounds on one turn, so a confused model cannot loop or fan out indefinitely.
    max_tool_calls_per_turn: int = 8
    # Cap on one tool result sent back to the model (free tiers meter tokens per minute).
    tool_result_max_chars: int = 4000
    max_model_calls_per_turn: int = 10

    history_messages: int = 16
    conversation_ttl_seconds: int = 3600

    chat_action_secret: str = ""
    action_ttl_seconds: int = 300
    action_result_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(env_file=SERVICE_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def check_secrets(self):
        if self.environment == "production":
            if self.secret_key == "changeme_dev_secret":
                raise ValueError("SECRET_KEY must be set to a real value in production")
            if not self.chat_action_secret:
                raise ValueError("CHAT_ACTION_SECRET must be set in production")
        return self

    @property
    def redis_uri(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def action_signing_key(self) -> bytes:
        """Dedicated key for confirmation tokens. In development it is derived from the JWT
        secret with a label, so it differs from it and a JWT can never double as a token."""
        if self.chat_action_secret:
            return self.chat_action_secret.encode()
        return hmac.new(self.secret_key.encode(), b"stockpilot-chat-action-v1", hashlib.sha256).digest()


settings = Settings()
