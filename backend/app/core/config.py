"""Application settings from environment (placeholders via .env.example)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+psycopg://field_service:change_me_local_only@localhost:5434/field_service"
    )
    api_host: str = "0.0.0.0"
    api_port: int = 8003
    cors_origins: str = "http://localhost:3003"
    demo_auth_enabled: bool = True
    secret_key: str = "replace_with_local_demo_secret"
    access_token_expire_minutes: int = 480
    ai_provider: str = "demo"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # M6 portal + hardening
    portal_link_expire_hours: int = 168  # 7 days
    rate_limit_login_per_minute: int = 20
    rate_limit_portal_per_minute: int = 20
    insights_connector_key: str | None = None
    environment: str = "demo"  # demo | production

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_placeholder_secret(self) -> bool:
        key = (self.secret_key or "").strip().lower()
        return key in {"", "replace_with_local_demo_secret", "changeme", "secret"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
