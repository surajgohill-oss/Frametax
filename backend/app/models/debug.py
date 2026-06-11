from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, Text, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ScraperErrorLog(Base):
    __tablename__ = "scraper_error_logs"
    __table_args__ = (
        Index("ix_scraper_errors_mp_ts", "marketplace", "timestamp"),
        Index("ix_scraper_errors_event", "event_id"),
        Index("ix_scraper_errors_type", "error_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marketplace: Mapped[str] = mapped_column(String(50), nullable=False)
    event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)
    selector: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_sample: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    html_snapshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "marketplace": self.marketplace, "event_id": self.event_id,
            "error_type": self.error_type, "selector": self.selector, "url": self.url,
            "http_status": self.http_status, "raw_sample": self.raw_sample,
            "screenshot_path": self.screenshot_path, "html_snapshot_path": self.html_snapshot_path,
            "extra": self.extra,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class FailureMemory(Base):
    __tablename__ = "failure_memory"
    __table_args__ = (
        Index("ix_failure_memory_mp_type", "marketplace", "error_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marketplace: Mapped[str] = mapped_column(String(50), nullable=False)
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)
    failed_pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    fallback_pattern: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fallback_success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=1)
    skip_failed: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_success: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "marketplace": self.marketplace, "error_type": self.error_type,
            "failed_pattern": self.failed_pattern, "fallback_pattern": self.fallback_pattern,
            "fallback_success_count": self.fallback_success_count, "failure_count": self.failure_count,
            "skip_failed": self.skip_failed,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }
