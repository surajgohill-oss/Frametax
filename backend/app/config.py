from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    app_name: str = "LA Concert Watchlist Tracker"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://concert:concert@db:5432/concert_tracker"
    database_sync_url: str = "postgresql://concert:concert@db:5432/concert_tracker"

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_asyncpg_driver(cls, v: str) -> str:
        """
        Railway (and some other hosts) inject DATABASE_URL as postgresql://
        which selects psycopg2.  SQLAlchemy's asyncio extension requires the
        asyncpg driver.  Normalise here so the app never depends on the host
        using the right prefix.
        """
        # Handle short 'postgres://' alias first, then the full prefix
        if isinstance(v, str):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            # Replace plain postgresql:// only (not already postgresql+asyncpg://)
            if "postgresql://" in v and "postgresql+asyncpg://" not in v:
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    redis_url: str = "redis://redis:6379/0"

    browser_data_dir: str = "/app/browser_sessions"
    screenshots_dir: str = "/app/debug_screenshots"
    html_snapshots_dir: str = "/app/debug_html"

    default_poll_interval_minutes: int = 60
    # Cap is intentionally high — limit by polling cost / scheduler health, not
    # an arbitrary count ceiling.  Set MAX_TRACKED_EVENTS in env to override.
    max_tracked_events: int = 500
    failure_cooldown_hours: int = 4

    stubhub_base_url: str = "https://www.stubhub.com"
    stubhub_api_key: str = ""
    seatgeek_base_url: str = "https://seatgeek.com"
    seatgeek_client_id: str = ""
    seatgeek_client_secret: str = ""
    ticketmaster_api_key: str = ""
    tickpick_api_key: str = ""
    gametime_api_key: str = ""
    vividseats_api_key: str = ""
    spotify_client_id: str = ""
    spotify_client_secret: str = ""

    env_mode: str = "prod"  # prod | mock

    # ── Event integrity controls ──────────────────────────────────────────────
    # DISCOVERY_FREEZE=true: discovery may scan/log but must not create Event or
    # TrackedEvent rows.  POST /api/events/ and TrackedEvent creation in hydrate
    # are also blocked.  Existing polling continues unaffected.
    discovery_freeze: bool = False

    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
