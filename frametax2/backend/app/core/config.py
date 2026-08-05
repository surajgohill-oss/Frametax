import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, field_validator
from typing import Any

# Phase A found /tmp/frametax2/storage non-durable (does not survive reboot).
# Phase B moves the default to a real, per-user application-data directory,
# matching the ~/.awardradar convention used by the sibling project.
DEFAULT_LOCAL_STORAGE_PATH = os.path.expanduser("~/.cineglobe/storage")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "FrameTax 2.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://frametax:frametax@localhost:5432/frametax2"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis / RQ
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage
    STORAGE_BACKEND: str = "local"  # "local" | "s3"
    LOCAL_STORAGE_PATH: str = DEFAULT_LOCAL_STORAGE_PATH
    S3_BUCKET: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""

    # Anthropic (LLM-assisted extraction only — not for final math)
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-6"
    LLM_MAX_TOKENS: int = 4096

    # FX rate source
    FX_API_URL: str = "https://open.er-api.com/v6/latest/USD"
    FX_REFRESH_INTERVAL_HOURS: int = 6

    # Security
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()

# Create the durable storage root if missing. Safe: exist_ok=True, never
# touches or moves any existing user file, only ensures the destination
# directory CineGlobe's own cached copies will eventually live in actually
# exists. No document is ingested here — this is the foundation only.
if settings.STORAGE_BACKEND == "local":
    os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)


def get_settings() -> Settings:
    return settings
