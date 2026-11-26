"""Application settings from environment (placeholders via .env.example)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+psycopg://field_service:change_me_local_only@localhost:5432/field_service"
    )
    api_host: str = "0.0.0.0"
    api_port: int = 8003
    cors_origins: str = "http://localhost:3003"
    demo_auth_enabled: bool = True
    secret_key: str = "replace_with_local_demo_secret"
    ai_provider: str = "demo"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
