from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), extra="ignore")

    database_url: str = Field(
        default="postgresql+psycopg://tokomate:tokomate_dev@localhost:5432/tokomate",
        description="SQLAlchemy PostgreSQL connection string",
    )
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    ollama_timeout_seconds: float = 120
    cors_origins: str = "http://localhost:3000"
    jwt_secret: str = "tokomate-local-demo-secret-change-before-production"
    jwt_access_token_minutes: int = 480
    demo_agent_email: str = "agent@tokomate.local"
    demo_agent_password: str = "DemoAgent123!"
    demo_admin_email: str = "admin@tokomate.local"
    demo_admin_password: str = "DemoAdmin123!"
    demo_order_verification_code: str = "TOKO192"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
