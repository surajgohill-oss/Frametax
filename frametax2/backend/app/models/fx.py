import uuid
from datetime import datetime
from sqlalchemy import String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class FXRate(Base):
    """
    FX rates fetched from open.er-api.com or similar.
    Keyed by base_currency / quote_currency / effective_date.
    All calculations use the rate closest to the project shoot date.
    """
    __tablename__ = "fx_rates"

    base_currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    quote_currency: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    rate: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    effective_date: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # ISO date string YYYY-MM-DD
    source: Mapped[str] = mapped_column(String(255), default="open.er-api.com")
