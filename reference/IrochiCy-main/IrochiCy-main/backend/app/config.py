"""
Application configuration via pydantic-settings.
All services default to localhost — single-machine dev setup.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings read from backend/.env file."""

    # ── PostgreSQL ──────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "sih26145"
    postgres_user: str
    postgres_password: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ───────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str

    @property
    def redis_url(self) -> str:
        return (
            f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        )

    # ── Redpanda / Kafka ────────────────────────────────────────
    redpanda_brokers: str = "localhost:9092"

    # ── JWT ──────────────────────────────────────────────────────
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_seconds: int = 900        # 15 minutes
    refresh_token_expire_seconds: int = 604800     # 7 days

    # ── Application ─────────────────────────────────────────────
    fastapi_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]
    environment: str = "development"

    # ── First-run admin (read once at startup, then ignored) ────
    initial_admin_username: str = "admin"
    initial_admin_password: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
