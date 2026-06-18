"""
apply_fx_rates.py

Converts amounts from local currency to USD using stored FX rates.
Rates are loaded from the fx_rates table, not fetched live during calculation.
Live fetch populates the table; calculations use snapshots.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

ENGINE_VERSION = "0.1.0"


@dataclass
class FXConversionResult:
    source_currency: str
    target_currency: str
    source_amount: float
    target_amount: float
    rate_used: float
    rate_date: str
    engine_version: str = ENGINE_VERSION


def convert_to_usd(
    amount: float,
    source_currency: str,
    fx_rates: dict[str, float],
    rate_date: str = "latest",
) -> FXConversionResult:
    """
    Convert amount from source_currency to USD.
    fx_rates: {currency_code: rate_vs_usd} — e.g. {"GBP": 0.7927, "CAD": 1.3612}
    """
    if source_currency.upper() == "USD":
        return FXConversionResult(
            source_currency="USD",
            target_currency="USD",
            source_amount=amount,
            target_amount=amount,
            rate_used=1.0,
            rate_date=rate_date,
        )

    rate = fx_rates.get(source_currency.upper())
    if rate is None:
        raise ValueError(f"No FX rate available for {source_currency}")

    # rate is quote_currency_per_usd (e.g. GBP per USD = 0.7927)
    # to convert GBP to USD: USD = GBP / rate
    usd_amount = float(amount) / float(rate)

    return FXConversionResult(
        source_currency=source_currency.upper(),
        target_currency="USD",
        source_amount=amount,
        target_amount=usd_amount,
        rate_used=rate,
        rate_date=rate_date,
    )


def convert_usd_to_local(
    amount_usd: float,
    target_currency: str,
    fx_rates: dict[str, float],
    rate_date: str = "latest",
) -> FXConversionResult:
    """
    Convert USD amount to local currency.
    """
    if target_currency.upper() == "USD":
        return FXConversionResult(
            source_currency="USD",
            target_currency="USD",
            source_amount=amount_usd,
            target_amount=amount_usd,
            rate_used=1.0,
            rate_date=rate_date,
        )

    rate = fx_rates.get(target_currency.upper())
    if rate is None:
        raise ValueError(f"No FX rate available for {target_currency}")

    local_amount = float(amount_usd) * float(rate)

    return FXConversionResult(
        source_currency="USD",
        target_currency=target_currency.upper(),
        source_amount=amount_usd,
        target_amount=local_amount,
        rate_used=rate,
        rate_date=rate_date,
    )
