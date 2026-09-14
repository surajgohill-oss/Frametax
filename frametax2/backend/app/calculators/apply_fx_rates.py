"""
apply_fx_rates.py

Converts amounts from local currency to USD using stored FX rates.
Rates are loaded from the fx_rates table, not fetched live during calculation.
Live fetch populates the table; calculations use snapshots.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping

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


# ── Canonical, immutable, project-selected FX context (Codex final P0 —
# canonical_fx) ──────────────────────────────────────────────────────────
#
# Root cause of Codex's finding ("Cap/threshold helpers read mutable
# global live date; missing/zero rates raise; negative rates produce
# negative economics; stale state ignored"): program_rate_rules.py's
# _fx_native_amount()/convert_incentive_cap_to_usd() imported
# production_normalization.FX_LIVE_SNAPSHOT_DATE/FX_RATE_SNAPSHOTS FRESH
# on every single call — a mutable module-global, not a value pinned once
# per evaluation. Two consequences, both real: (1) if a live FX refresh
# (app/services/fx_refresh.py) mutates FX_LIVE_SNAPSHOT_DATE between two
# calls within the SAME canonical evaluation, different candidates in the
# same result could silently be priced against different snapshots; (2)
# convert_to_usd/convert_usd_to_local RAISE on a missing rate and divide
# by whatever rate is present with NO validation — a zero rate raises
# ZeroDivisionError, a corrupted negative rate silently produces a
# negative cap/incentive, and a live-refresh failure (FX_FRESHNESS_STATUS
# == "stale_fallback") was never even consulted.
#
# CanonicalFXContext is an explicit, immutable, single-snapshot value —
# built ONCE (by production_normalization.build_fx_context()) and passed
# down through resolve_program_rate()/price_segment()/
# _resolve_incentive_dollar_cap() as a plain function argument, never
# re-read from a global mid-calculation. `rates` is always a fresh COPY
# of the source snapshot dict (never a live reference into a table a
# later live refresh could mutate), so a context, once built, can never
# change under the caller.
FX_STATUS_RESOLVED = "RESOLVED"
FX_STATUS_MISSING = "MISSING_RATE"
FX_STATUS_NONPOSITIVE = "NONPOSITIVE_RATE"
FX_STATUS_NONFINITE = "NONFINITE_RATE"
FX_STATUS_STALE_UNACCEPTED = "STALE_UNACCEPTED_SNAPSHOT"


def _is_finite_positive(value) -> bool:
    """True only for a real, finite, strictly-positive number. Rejects
    None, NaN, +inf, -inf, and any non-numeric type -- the single shared
    predicate every calculation-driving numeric input (an FX rate, an
    awarded rate, a QSAPPE amount, a prior-award aggregate) must satisfy
    before it may participate in arithmetic. `bool` is explicitly
    excluded even though `isinstance(True, int)` is true in Python --
    a boolean fact was never meant to be read as a numeric rate/amount."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    value = float(value)
    return math.isfinite(value) and value > 0.0


def _is_finite(value) -> bool:
    """True only for a real, finite number (may be zero or negative) --
    used where the domain itself decides whether zero/negative is a
    valid or invalid value, after this shared finiteness gate."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


@dataclass(frozen=True)
class CanonicalFXContext:
    """One DEEPLY immutable, explicit FX snapshot selected for a single
    canonical evaluation (or, for a caller not yet threading a project-
    level context, for a single call) — see production_normalization.
    build_fx_context(), the ONE place this reads the live mutable global,
    exactly once, into this frozen value.

    Codex adverse finding (P0-FX-001): a `@dataclass(frozen=True)`
    wrapper only blocks REASSIGNING the `rates` attribute
    (`ctx.rates = {...}` raises) — it does nothing to stop MUTATING the
    dict `rates` already points at (`ctx.rates["EUR"] = 9.99` silently
    succeeds against a plain `dict`). `__post_init__` below coerces
    whatever mapping is supplied into a `types.MappingProxyType` wrapping
    a fresh, defensively-copied `dict` — a read-only VIEW that raises
    `TypeError` on any item assignment/deletion, and one no caller can
    ever get a mutable handle back to (the proxy is the only thing
    stored; the original dict is never retained)."""
    snapshot_date: str
    rates: "Mapping[str, float]"   # currency -> local units per USD; a deeply frozen VIEW
    source: str
    #: "fresh" | "stale_fallback" | "never_refreshed" — see
    #: production_normalization.FX_FRESHNESS_STATUS. A HISTORICAL
    #: (deliberately-dated, non-live) context is always "fresh": staleness
    #: is a property of the LIVE refresh pipeline having failed, not of a
    #: deliberately-chosen historical date.
    freshness_status: str = "never_refreshed"

    def __post_init__(self) -> None:
        # object.__setattr__ is required here specifically BECAUSE the
        # dataclass is frozen -- this is the one sanctioned place a
        # frozen dataclass may still initialize/normalize its own
        # fields, never a general mutation escape hatch.
        object.__setattr__(self, "rates", MappingProxyType(dict(self.rates)))


@dataclass(frozen=True)
class FXRateResolution:
    """Typed, NEVER-raised outcome of resolving one currency's rate
    against a CanonicalFXContext. Replaces convert_to_usd/
    convert_usd_to_local's raise-on-missing and unguarded division for
    every cap/threshold evaluation path, which must fail CLOSED (a typed
    non-priceable disposition disclosed in the trace) rather than crash
    the request or silently compute nonsense (negative/zero-derived)
    economics."""
    status: str   # FX_STATUS_*
    currency: str
    rate: float | None
    snapshot_date: str
    source: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.status == FX_STATUS_RESOLVED


def resolve_fx_rate(context: CanonicalFXContext, currency: str) -> FXRateResolution:
    """The one place a currency's rate is validated against an explicit
    CanonicalFXContext. Never raises; always returns a typed disposition.
    USD needs no rate — accepted currency itself is implicitly USD-safe."""
    currency = currency.upper()
    if currency == "USD":
        return FXRateResolution(
            status=FX_STATUS_RESOLVED, currency="USD", rate=1.0,
            snapshot_date=context.snapshot_date, source=context.source,
            detail="USD requires no conversion.",
        )
    if context.freshness_status == "stale_fallback":
        return FXRateResolution(
            status=FX_STATUS_STALE_UNACCEPTED, currency=currency, rate=None,
            snapshot_date=context.snapshot_date, source=context.source,
            detail=(
                f"FX context '{context.snapshot_date}' is flagged stale_fallback "
                "(a live refresh previously failed and this snapshot was retained "
                "for disclosure rather than silently marked fresh — see "
                "production_normalization.mark_fx_refresh_failed) — rejected for "
                "a new economic calculation, never silently consumed."
            ),
        )
    rate = context.rates.get(currency)
    if rate is None:
        return FXRateResolution(
            status=FX_STATUS_MISSING, currency=currency, rate=None,
            snapshot_date=context.snapshot_date, source=context.source,
            detail=f"No sourced FX rate for {currency} in the {context.snapshot_date} snapshot.",
        )
    # Codex adverse finding (P0-FX-001): the prior check was `rate <= 0`
    # only — NaN and +infinity both fail EVERY comparison against 0
    # (`float('nan') <= 0` is False, `float('inf') <= 0` is False), so
    # both silently fell through to RESOLVED and were then used in real
    # division/multiplication, producing NaN/infinite economics. Checking
    # `math.isfinite()` FIRST, before any sign check, closes this: NaN,
    # +inf, and -inf are all rejected as NONFINITE_RATE before a
    # NONPOSITIVE_RATE check is even reached.
    if not math.isfinite(rate):
        return FXRateResolution(
            status=FX_STATUS_NONFINITE, currency=currency, rate=rate,
            snapshot_date=context.snapshot_date, source=context.source,
            detail=(
                f"Rate for {currency} on {context.snapshot_date} is not finite "
                f"({rate}) — NaN/+inf/-inf is corrupted/invalid data, never used "
                "to compute economics."
            ),
        )
    if rate <= 0:
        return FXRateResolution(
            status=FX_STATUS_NONPOSITIVE, currency=currency, rate=rate,
            snapshot_date=context.snapshot_date, source=context.source,
            detail=(
                f"Rate for {currency} on {context.snapshot_date} is non-positive "
                f"({rate}) — corrupted/invalid data, never used to compute economics."
            ),
        )
    return FXRateResolution(
        status=FX_STATUS_RESOLVED, currency=currency, rate=rate,
        snapshot_date=context.snapshot_date, source=context.source,
        detail=f"Resolved {currency} rate {rate} from {context.snapshot_date} ({context.source}).",
    )


def convert_to_usd_ctx(
    amount: float, source_currency: str, context: CanonicalFXContext,
) -> tuple[FXConversionResult | None, FXRateResolution]:
    """Context-based, never-raising sibling of convert_to_usd(). Returns
    (None, resolution) with a typed failure status when the rate cannot
    be safely resolved — the caller must treat that as non-priceable,
    never fall back to a guessed/implicit 1.0 rate."""
    res = resolve_fx_rate(context, source_currency)
    if not res.ok:
        return None, res
    usd_amount = float(amount) / float(res.rate)
    return FXConversionResult(
        source_currency=source_currency.upper(), target_currency="USD",
        source_amount=amount, target_amount=usd_amount, rate_used=res.rate,
        rate_date=context.snapshot_date,
    ), res


def convert_usd_to_local_ctx(
    amount_usd: float, target_currency: str, context: CanonicalFXContext,
) -> tuple[FXConversionResult | None, FXRateResolution]:
    """Context-based, never-raising sibling of convert_usd_to_local()."""
    res = resolve_fx_rate(context, target_currency)
    if not res.ok:
        return None, res
    local_amount = float(amount_usd) * float(res.rate)
    return FXConversionResult(
        source_currency="USD", target_currency=target_currency.upper(),
        source_amount=amount_usd, target_amount=local_amount, rate_used=res.rate,
        rate_date=context.snapshot_date,
    ), res
