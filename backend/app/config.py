from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "LA Concert Watchlist Tracker"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://concert:concert@db:5432/concert_tracker"
    database_sync_url: str = "postgresql://concert:concert@db:5432/concert_tracker"
    redis_url: str = "redis://redis:6379/0"

    browser_data_dir: str = "/app/browser_sessions"
    screenshots_dir: str = "/app/debug_screenshots"
    html_snapshots_dir: str = "/app/debug_html"

    default_poll_interval_minutes: int = 60
    max_tracked_events: int = 30
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

    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
