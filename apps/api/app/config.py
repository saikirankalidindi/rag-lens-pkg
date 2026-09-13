"""
Application configuration.

All settings are read from environment variables (or .env file in development).
Never hard-code secrets here.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://raglens:raglens@localhost:5432/raglens"
    )
    # Sync URL for Alembic; derived from database_url if not set explicitly
    database_sync_url: str = (
        "postgresql://raglens:raglens@localhost:5432/raglens"
    )

    # ── Security ──────────────────────────────────────────────────────────
    secret_key: str = "changeme-use-a-real-secret-in-production-min-32-chars"
    # Access token lifetime in minutes
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # ── CORS ──────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Ingestion limits ──────────────────────────────────────────────────
    max_trace_payload_bytes: int = 5 * 1024 * 1024  # 5 MB

    # ── Server ────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── Diagnostics thresholds (configurable) ────────────────────────────
    diag_low_retrieval_score_threshold: float = 0.70
    diag_slow_retrieval_ms: int = 500
    diag_excessive_context_pct: float = 0.80      # 80% of context window
    diag_slow_generation_pct: float = 0.85        # 85% of total trace duration
    diag_token_heavy_context_pct: float = 0.85    # 85% of input tokens
    diag_low_context_utilization_pct: float = 0.40
    diag_retrieval_waste_ratio: float = 3.0       # retrieved / selected ratio


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
