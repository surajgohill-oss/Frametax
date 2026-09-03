"""
fx_refresh.py

CineGlobe Overview FX Strip Freshness Architecture.

Wires the previously-dormant `fx_rates` table (app/models/fx.py, created
in migration 0001 but never read or written by any code path — confirmed
by inspection before this pass) up as the real canonical FX snapshot
persistence layer, and provides the ONE page-open freshness check every
project-state read goes through.

    USER OPENS/RELOADS A PRODUCTION
            |
       ensure_fx_freshness(session)   <- THIS MODULE, called once per
            |                            GET /projects/{id}/state
      in-process cache fresh?
       /            \\
     yes              no
      |                |
    reuse        acquire single-flight lock, re-check under lock
                        |
                 query fx_rates table for today's row-set
                  /                        \\
              complete                   missing/stale
                 |                            |
             adopt into                 live fetch (open.er-api.com,
          in-process cache             ALL tracked currencies, ONE
                 |                      request) -> upsert fx_rates ->
                 |                      adopt into in-process cache
                 |                            |
                 |                       (failure: keep last valid
                 |                        snapshot untouched, mark
                 |                        stale_fallback, disclose)
                  \\                        /
                   production_normalization.py's module-level
                   FX_RATE_SNAPSHOTS/FX_LIVE_SNAPSHOT_DATE — the ONE
                   state fx_rate_snapshot() reads, consumed identically
                   by the optimizer's FX-delta overlay AND the served
                   UI payload.

No parallel FX engine, no browser-side fetch: this is the only place a
live rate is ever requested, and it runs server-side, once, per
freshness check.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculators import production_normalization as fx_doctrine
from app.models.fx import FXRate

logger = logging.getLogger(__name__)

FX_REFRESH_VERSION = "1.0.0"

#: Freshness TTL — the narrowest sensible canonical policy: no existing
#: freshness doctrine was found anywhere in this codebase (FX_RATE_
#: SNAPSHOTS was a static one-time constant; apply_fx_rates.py's own
#: docstring only ever DESCRIBED a live-fetch/snapshot split, nothing
#: implemented or scheduled it). 24 hours is the standard daily-reference-
#: rate cadence every source this module reads (ECB, open.er-api.com)
#: itself publishes on, and matches the once-a-day granularity
#: FX_RATE_SNAPSHOTS has always stored (one dict per calendar date, never
#: intraday). Recorded here, centrally — no magic freshness number is
#: duplicated into the frontend or any other module.
FX_FRESHNESS_TTL_HOURS = 24

_PROVIDER_URL = "https://open.er-api.com/v6/latest/USD"
_PROVIDER_TIMEOUT_SECONDS = 8.0

# Single-flight protection (item 5): a process-local lock is sufficient
# here — this backend runs as one process per environment (no existing
# distributed-lock/queue infrastructure was found to reuse, and the
# unique constraint on fx_rates(base_currency, quote_currency,
# effective_date) is itself a second, DB-level safety net against two
# processes racing to insert the same day's row — the loser's insert
# becomes a harmless update). Documented limitation, not silently assumed
# sufficient for a multi-process deployment.
_refresh_lock = asyncio.Lock()

# In-process "already checked recently" cache, keyed by nothing (one
# snapshot serves every project) — avoids a DB round trip on every page
# load once warm within the TTL, per item 4 ("page open must not mean
# blind network fetch").
_last_checked_at: datetime | None = None


@dataclass(frozen=True)
class FXFreshnessStatus:
    is_fresh: bool
    refreshed_now: bool
    as_of: str
    source: str
    error: str | None


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _is_within_ttl(checked_at: datetime) -> bool:
    age = datetime.now(timezone.utc) - checked_at
    return age.total_seconds() < FX_FRESHNESS_TTL_HOURS * 3600


async def ensure_fx_freshness(session: AsyncSession) -> FXFreshnessStatus:
    """The single canonical entry point every page-open/reload path calls
    (GET /projects/{id}/state) before economics are read. Idempotent and
    safe to call unconditionally — see the module docstring's flowchart."""
    global _last_checked_at

    if _last_checked_at is not None and _is_within_ttl(_last_checked_at):
        return FXFreshnessStatus(
            is_fresh=True, refreshed_now=False,
            as_of=fx_doctrine.FX_LIVE_SNAPSHOT_DATE,
            source=fx_doctrine.FX_LIVE_SNAPSHOT_SOURCE, error=None,
        )

    async with _refresh_lock:
        # Re-check inside the lock: a concurrent request may have already
        # refreshed while this one waited (single-flight, item 5).
        if _last_checked_at is not None and _is_within_ttl(_last_checked_at):
            return FXFreshnessStatus(
                is_fresh=True, refreshed_now=False,
                as_of=fx_doctrine.FX_LIVE_SNAPSHOT_DATE,
                source=fx_doctrine.FX_LIVE_SNAPSHOT_SOURCE, error=None,
            )

        db_status = await _adopt_from_db_if_fresh(session)
        if db_status is not None:
            _last_checked_at = datetime.now(timezone.utc)
            return db_status

        status = await _refresh_from_provider(session)
        _last_checked_at = datetime.now(timezone.utc)
        return status


async def _adopt_from_db_if_fresh(session: AsyncSession) -> FXFreshnessStatus | None:
    """A cold process (just restarted) has no in-process history but may
    already have a same-day snapshot another process/request persisted —
    reuse it rather than re-hitting the provider. Returns None (falls
    through to a live refresh) when the persisted snapshot is missing,
    stale, or incomplete for a required currency."""
    today = _today_str()
    rows = (await session.execute(
        select(FXRate).where(
            FXRate.base_currency == "USD",
            FXRate.effective_date == today,
        )
    )).scalars().all()
    if not rows:
        return None
    have = {r.quote_currency: float(r.rate) for r in rows}
    if not fx_doctrine.ALL_TRACKED_CURRENCIES.issubset(have.keys()):
        return None  # incomplete pair coverage — refresh to fill the gap
    source = rows[0].source or fx_doctrine.FX_LIVE_SNAPSHOT_SOURCE
    fx_doctrine.apply_live_fx_snapshot(today, have, source)
    return FXFreshnessStatus(is_fresh=True, refreshed_now=False, as_of=today, source=source, error=None)


async def _fetch_provider_payload() -> dict:
    """Isolated so tests can monkeypatch this one function (same
    convention as talent_nationality_resolution.py's own network-boundary
    helpers) instead of mocking httpx/the network — no mocking library is
    installed or used elsewhere in this repo."""
    async with httpx.AsyncClient(timeout=_PROVIDER_TIMEOUT_SECONDS) as client:
        resp = await client.get(_PROVIDER_URL)
        resp.raise_for_status()
        return resp.json()


async def _refresh_from_provider(session: AsyncSession) -> FXFreshnessStatus:
    today = _today_str()
    try:
        payload = await _fetch_provider_payload()
        if payload.get("result") != "success":
            raise ValueError(f"provider reported non-success result: {payload.get('result')!r}")
        provider_rates = payload.get("rates") or {}
        rates = {
            code: float(provider_rates[code])
            for code in fx_doctrine.ALL_TRACKED_CURRENCIES
            if code in provider_rates
        }
        missing = fx_doctrine.ALL_TRACKED_CURRENCIES - rates.keys()
        if missing:
            logger.warning("fx_refresh: provider omitted %s — persisting the rest, never fabricating these", sorted(missing))
        if not rates:
            raise ValueError("provider returned no rates for any tracked currency")

        await _upsert_rates(session, today, rates, "open.er-api.com")
        await session.commit()
        fx_doctrine.apply_live_fx_snapshot(today, rates, "open.er-api.com")
        return FXFreshnessStatus(is_fresh=True, refreshed_now=True, as_of=today, source="open.er-api.com", error=None)
    except Exception as exc:  # noqa: BLE001 — any provider/network failure must fall back truthfully, never crash the page
        await session.rollback()
        error = f"{type(exc).__name__}: {exc}"
        logger.warning("fx_refresh: live refresh failed, retaining last valid snapshot (%s)", error)
        fx_doctrine.mark_fx_refresh_failed(error)
        return FXFreshnessStatus(
            is_fresh=False, refreshed_now=False,
            as_of=fx_doctrine.FX_LIVE_SNAPSHOT_DATE,
            source=fx_doctrine.FX_LIVE_SNAPSHOT_SOURCE, error=error,
        )


async def _upsert_rates(session: AsyncSession, effective_date: str, rates: dict[str, float], source: str) -> None:
    """Get-or-update per currency against the pre-existing unique
    constraint (base_currency, quote_currency, effective_date) — a plain
    portable SELECT-then-write rather than a dialect-specific ON
    CONFLICT, since this runs at most once per tracked currency per day
    (no meaningful write-volume concern)."""
    existing_rows = (await session.execute(
        select(FXRate).where(FXRate.base_currency == "USD", FXRate.effective_date == effective_date)
    )).scalars().all()
    existing_by_currency = {r.quote_currency: r for r in existing_rows}
    for currency, rate in rates.items():
        row = existing_by_currency.get(currency)
        if row is not None:
            row.rate = rate
            row.source = source
        else:
            session.add(FXRate(
                base_currency="USD", quote_currency=currency, rate=rate,
                effective_date=effective_date, source=source,
            ))
