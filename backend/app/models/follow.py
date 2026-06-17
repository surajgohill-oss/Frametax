from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class UserFollow(Base):
    __tablename__ = "user_follows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)   # "artist" | "team"
    entity_key: Mapped[str] = mapped_column(String(255), nullable=False)   # normalized lowercase key
    display_name: Mapped[str] = mapped_column(String(500), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)    # "next3"|"next5"|"next10"|"all_future"
    scope_anchor: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
