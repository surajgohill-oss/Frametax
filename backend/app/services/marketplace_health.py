"""
marketplace_health.py — Canonical Marketplace Health Model

Derives health status from runtime data only (tracked_events + poll_runs + listings).
No guessing. No hardcoded lists of "known broken" marketplaces.

Health Status Definitions
──────────────────────────────────────────────────────────────
POPULATED           listings > 0 AND last poll within cadence
STALE               listings > 0 BUT last success > 2x cadence ago
ID_RESOLVED_PENDING_POLL  has external_event_id, 0 listings, poll ran but returned 0
AUTOMATED_RESOLUTION_FAILED  poll ran, error="unresolved_event_id", no external_event_id
NEEDS_MARKETPLACE_URL  no external_event_id, no external_url in tracked_events
BLOCKED             consecutive failures / timeouts > 5, never returned listings
NO_DATA             poll succeeded, 0 listings (event may have no inventory)

Warning Levels
──────────────
GREEN    = POPULATED (data in hand)
YELLOW   = STALE | ID_RESOLVED_PENDING_POLL | NO_DATA
RED      = AUTOMATED_RESOLUTION_FAILED | NEEDS_MARKETPLACE_URL | BLOCKED

Coverage Classification
────────────────────────
FULL     = 4+ marketplaces POPULATED
PARTIAL  = 2-3 marketplaces POPULATED
LIMITED  = 1 marketplace POPULATED
BROKEN   = 0 marketplaces POPULATED
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Core marketplaces for coverage scoring.  SeatGeek and TicketMaster are
# tracked/displayed but excluded from the core health / coverage score.
_CORE_MARKETPLACES = {"gametime", "stubhub", "tickpick", "vividseats"}


def _f(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# Cadence multiplier: mark STALE when last success is older than cadence × this
_STALE_MULTIPLIER = 2.0

# Consecutive-failure threshold for BLOCKED
_BLOCKED_FAILURE_THRESHOLD = 5


def _classify_status(
    external_event_id: Optional[str],
    external_url: Optional[str],
    slug: str,
    active_listings: int,
    last_polled_at: Optional[datetime],
    poll_interval_minutes: Optional[int],
    last_poll_status: Optional[str],
    last_poll_error: Optional[str],
    last_poll_listings: Optional[int],
    consecutive_failures: int,
    total_polls: int,
    total_successes: int,
    now_naive: datetime,
) -> tuple[str, str, Optional[str]]:
    """
    Returns (status, warning_level, remediation).
    All inputs are plain Python values; no DB access here.
    """
    has_id  = bool(external_event_id and external_event_id.strip())
    has_url = bool(external_url and external_url.strip())
    cadence_hours = (poll_interval_minutes or 1440) / 60.0
    staleness_threshold_hours = cadence_hours * _STALE_MULTIPLIER

    freshness_hours: Optional[float] = None
    if last_polled_at:
        freshness_hours = (now_naive - last_polled_at.replace(tzinfo=None)).total_seconds() / 3600

    # ── Never been polled ────────────────────────────────────────────────────
    if total_polls == 0 or last_polled_at is None:
        if not has_id and not has_url:
            return "NEEDS_MARKETPLACE_URL", "RED", f"No external ID or URL. Add via POST /api/events/{{event_id}}/tracked with external_url."
        if has_id:
            return "ID_RESOLVED_PENDING_POLL", "YELLOW", "Awaiting first collector run."
        return "NEEDS_MARKETPLACE_URL", "RED", "No external ID resolved yet."

    # ── No external ID / URL (structural block) ──────────────────────────────
    if not has_id:
        if last_poll_error and "unresolved_event_id" in (last_poll_error or ""):
            return "AUTOMATED_RESOLUTION_FAILED", "RED", "Automated ID resolution failed. Provide URL manually via /url-intake."
        if not has_url:
            return "NEEDS_MARKETPLACE_URL", "RED", "No external ID or URL. Add via POST /api/events/{event_id}/tracked."
        # Has URL but no ID — resolver hasn't extracted yet
        return "ID_RESOLVED_PENDING_POLL", "YELLOW", "URL present; awaiting ID extraction on next poll."

    # ── BLOCKED: many polls, no listings, high failure rate ─────────────────
    if total_polls >= 5 and total_successes == 0:
        return "BLOCKED", "RED", "All polls have failed — possible auth/API limitation. No automated remediation."

    if consecutive_failures >= _BLOCKED_FAILURE_THRESHOLD and active_listings == 0:
        return "BLOCKED", "RED", f"{consecutive_failures} consecutive failures. Check collector service for {slug}."

    # ── POPULATED or STALE ───────────────────────────────────────────────────
    if active_listings > 0:
        if freshness_hours is not None and freshness_hours > staleness_threshold_hours:
            return "STALE", "YELLOW", f"Last poll {freshness_hours:.1f}h ago (cadence: {cadence_hours:.0f}h). Check collector service."
        return "POPULATED", "GREEN", None

    # ── ID resolved, polled, 0 listings ─────────────────────────────────────
    if has_id:
        if last_poll_status == "success":
            return "NO_DATA", "YELLOW", "Collector ran successfully but returned 0 listings. Event may have no inventory."
        if last_poll_error and "unresolved_event_id" in (last_poll_error or ""):
            return "AUTOMATED_RESOLUTION_FAILED", "RED", "Automated ID resolution failed. Provide URL manually via /url-intake."
        if last_poll_status in ("error", "timeout") and total_successes == 0:
            return "BLOCKED", "RED", f"Polls failing (status={last_poll_status}). Check collector for {slug}."
        # Has ID, polled, 0 listings but not an obvious error — pending
        return "ID_RESOLVED_PENDING_POLL", "YELLOW", "ID resolved. Awaiting successful poll with inventory data."

    return "NO_DATA", "YELLOW", "No inventory data yet."


async def get_event_marketplace_health(event_id: int, db: AsyncSession) -> dict:
    """
    Returns full marketplace health for a single event.
    """
    now_utc  = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)

    rows = (await db.execute(text("""
        SELECT
            m.slug,
            m.id AS marketplace_id,
            te.external_event_id,
            te.external_url,
            te.last_polled_at,
            te.poll_interval_minutes,
            te.consecutive_zero_inventory_count,
            COUNT(DISTINCT l.id)                                         AS active_listings,
            -- Latest poll run info
            (SELECT pr.status
             FROM poll_runs pr WHERE pr.tracked_event_id = te.id
             ORDER BY pr.completed_at DESC LIMIT 1)                      AS last_status,
            (SELECT pr.listings_found
             FROM poll_runs pr WHERE pr.tracked_event_id = te.id
             ORDER BY pr.completed_at DESC LIMIT 1)                      AS last_listings_found,
            (SELECT pr.error_message
             FROM poll_runs pr WHERE pr.tracked_event_id = te.id
             ORDER BY pr.completed_at DESC LIMIT 1)                      AS last_error,
            (SELECT pr.completed_at
             FROM poll_runs pr WHERE pr.tracked_event_id = te.id
             ORDER BY pr.completed_at DESC LIMIT 1)                      AS last_completed_at,
            COUNT(DISTINCT pr_all.id)                                    AS total_polls,
            SUM(CASE WHEN pr_all.status = 'success' THEN 1 ELSE 0 END)  AS total_successes,
            SUM(CASE WHEN pr_all.status IN ('error','timeout') THEN 1 ELSE 0 END) AS total_failures
        FROM tracked_events te
        JOIN marketplaces m ON m.id = te.marketplace_id
        LEFT JOIN listings l   ON l.event_id = te.event_id
                               AND l.marketplace_id = te.marketplace_id
                               AND l.is_active = true
        LEFT JOIN poll_runs pr_all ON pr_all.tracked_event_id = te.id
        WHERE te.event_id = :eid AND te.is_active = true
        GROUP BY m.slug, m.id, te.external_event_id, te.external_url,
                 te.last_polled_at, te.poll_interval_minutes,
                 te.consecutive_zero_inventory_count, te.id
        ORDER BY m.slug
    """), {"eid": event_id})).fetchall()

    marketplaces_out = []
    for row in rows:
        slug            = row.slug
        active_listings = int(row.active_listings or 0)
        total_polls     = int(row.total_polls or 0)
        total_successes = int(row.total_successes or 0)
        total_failures  = int(row.total_failures or 0)
        consec_zero     = int(row.consecutive_zero_inventory_count or 0)

        freshness_hours = None
        if row.last_polled_at:
            lp = row.last_polled_at.replace(tzinfo=None) if row.last_polled_at.tzinfo else row.last_polled_at
            freshness_hours = round((now_naive - lp).total_seconds() / 3600, 1)

        status, warning_level, remediation = _classify_status(
            external_event_id   = row.external_event_id,
            external_url        = row.external_url,
            slug                = slug,
            active_listings     = active_listings,
            last_polled_at      = row.last_polled_at,
            poll_interval_minutes = row.poll_interval_minutes,
            last_poll_status    = row.last_status,
            last_poll_error     = row.last_error,
            last_poll_listings  = row.last_listings_found,
            consecutive_failures = total_failures,
            total_polls         = total_polls,
            total_successes     = total_successes,
            now_naive           = now_naive,
        )

        marketplaces_out.append({
            "marketplace":          slug,
            "is_core":              slug in _CORE_MARKETPLACES,
            "status":               status,
            "warning_level":        warning_level,
            "external_id_present":  bool(row.external_event_id and row.external_event_id.strip()),
            "external_url_present": bool(row.external_url and row.external_url.strip()),
            "listings_count":       active_listings,
            "freshness_hours":      freshness_hours,
            "last_poll_at":         row.last_completed_at.isoformat() if row.last_completed_at else None,
            "last_poll_status":     row.last_status,
            "poll_cadence_hours":   round((row.poll_interval_minutes or 1440) / 60, 1),
            "total_polls":          total_polls,
            "total_successes":      total_successes,
            "total_failures":       total_failures,
            "remediation":          remediation,
        })

    core_mps      = [m for m in marketplaces_out if m["is_core"]]
    core_populated = [m for m in core_mps if m["status"] == "POPULATED"]

    # Coverage classification uses CORE marketplaces only
    core_pop_count = len(core_populated)
    if core_pop_count >= 4:
        core_coverage = "FULL"
    elif core_pop_count >= 2:
        core_coverage = "PARTIAL"
    elif core_pop_count == 1:
        core_coverage = "LIMITED"
    else:
        core_coverage = "BROKEN"

    return {
        "event_id":     event_id,
        "computed_at":  now_utc.isoformat(),
        "marketplaces": marketplaces_out,
        "summary": {
            "total_marketplaces":  len(marketplaces_out),
            "core_marketplaces":   len(core_mps),
            "populated":           sum(1 for m in marketplaces_out if m["status"] == "POPULATED"),
            "core_populated":      core_pop_count,
            "core_coverage":       core_coverage,
            "green":   sum(1 for m in core_mps if m["warning_level"] == "GREEN"),
            "yellow":  sum(1 for m in core_mps if m["warning_level"] == "YELLOW"),
            "red":     sum(1 for m in core_mps if m["warning_level"] == "RED"),
        },
    }


async def get_coverage_audit(db: AsyncSession) -> dict:
    """
    Returns marketplace health + coverage classification for ALL active future events.
    """
    now_utc   = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)

    # Batch query: all active future events × marketplaces
    rows = (await db.execute(text("""
        SELECT
            e.id                                                          AS event_id,
            e.title,
            e.event_date,
            m.slug,
            te.external_event_id,
            te.external_url,
            te.last_polled_at,
            te.poll_interval_minutes,
            COUNT(DISTINCT l.id)                                          AS active_listings,
            (SELECT pr.status
             FROM poll_runs pr WHERE pr.tracked_event_id = te.id
             ORDER BY pr.completed_at DESC LIMIT 1)                       AS last_status,
            (SELECT pr.error_message
             FROM poll_runs pr WHERE pr.tracked_event_id = te.id
             ORDER BY pr.completed_at DESC LIMIT 1)                       AS last_error,
            COUNT(DISTINCT pr_all.id)                                     AS total_polls,
            SUM(CASE WHEN pr_all.status = 'success' THEN 1 ELSE 0 END)   AS total_successes,
            SUM(CASE WHEN pr_all.status IN ('error','timeout') THEN 1 ELSE 0 END) AS total_failures
        FROM events e
        JOIN tracked_events te ON te.event_id = e.id AND te.is_active = true
        JOIN marketplaces m    ON m.id = te.marketplace_id
        LEFT JOIN listings l   ON l.event_id = e.id
                               AND l.marketplace_id = te.marketplace_id
                               AND l.is_active = true
        LEFT JOIN poll_runs pr_all ON pr_all.tracked_event_id = te.id
        WHERE e.event_date > :now
        GROUP BY e.id, e.title, e.event_date, m.slug,
                 te.external_event_id, te.external_url,
                 te.last_polled_at, te.poll_interval_minutes, te.id
        ORDER BY e.event_date, e.id, m.slug
    """), {"now": now_naive})).fetchall()

    # Group by event
    events: dict[int, dict] = {}
    for row in rows:
        eid = row.event_id
        if eid not in events:
            events[eid] = {
                "event_id":   eid,
                "title":      row.title,
                "event_date": row.event_date.date().isoformat() if row.event_date else None,
                "marketplaces": [],
            }

        active_listings = int(row.active_listings or 0)
        total_polls     = int(row.total_polls or 0)
        total_successes = int(row.total_successes or 0)
        total_failures  = int(row.total_failures or 0)

        status, warning_level, remediation = _classify_status(
            external_event_id   = row.external_event_id,
            external_url        = row.external_url,
            slug                = row.slug,
            active_listings     = active_listings,
            last_polled_at      = row.last_polled_at,
            poll_interval_minutes = row.poll_interval_minutes,
            last_poll_status    = row.last_status,
            last_poll_error     = row.last_error,
            last_poll_listings  = None,
            consecutive_failures = total_failures,
            total_polls         = total_polls,
            total_successes     = total_successes,
            now_naive           = now_naive,
        )

        events[eid]["marketplaces"].append({
            "marketplace":   row.slug,
            "is_core":       row.slug in _CORE_MARKETPLACES,
            "status":        status,
            "warning_level": warning_level,
            "listings":      active_listings,
            "remediation":   remediation,
        })

    # Build coverage summary per event
    event_list = []
    for eid, ev in events.items():
        core_mps        = [m for m in ev["marketplaces"] if m["is_core"]]
        populated_count = sum(1 for m in core_mps if m["status"] == "POPULATED")
        total_mps       = len(core_mps)
        populated_mps   = [m["marketplace"] for m in core_mps if m["status"] == "POPULATED"]
        missing_mps     = [m["marketplace"] for m in core_mps if m["status"] != "POPULATED"]

        if populated_count >= 4:
            coverage = "FULL"
        elif populated_count >= 2:
            coverage = "PARTIAL"
        elif populated_count == 1:
            coverage = "LIMITED"
        else:
            coverage = "BROKEN"

        coverage_pct = round(populated_count / total_mps * 100) if total_mps > 0 else 0

        event_list.append({
            "event_id":          eid,
            "title":             ev["title"],
            "event_date":        ev["event_date"],
            "coverage":          coverage,
            "coverage_pct":      coverage_pct,
            "populated_count":   populated_count,
            "marketplace_count": total_mps,
            "populated_marketplaces": populated_mps,
            "missing_coverage":  missing_mps,
            "marketplace_detail": ev["marketplaces"],
        })

    # Global summary
    coverage_counts = {c: sum(1 for e in event_list if e["coverage"] == c)
                       for c in ("FULL", "PARTIAL", "LIMITED", "BROKEN")}

    return {
        "audit_at":     now_utc.isoformat(),
        "total_events": len(event_list),
        "summary":      coverage_counts,
        "events":       event_list,
    }


async def get_event_alerts(event_id: int, db: AsyncSession) -> dict:
    """
    Generates health alerts for a single event.
    Returns structured alerts + human-readable messages.

    Alert types:
      MARKETPLACE_STALE
      MARKETPLACE_BLOCKED
      MARKETPLACE_PENDING
      LOW_COVERAGE
      NEEDS_URL
      RESOLUTION_FAILED
    """
    health = await get_event_marketplace_health(event_id, db)
    now_utc = datetime.now(timezone.utc)

    alerts = []
    populated = health["summary"]["core_populated"]
    total     = health["summary"]["core_marketplaces"]

    for mp in health["marketplaces"]:
        # Only emit alerts for core marketplaces
        if not mp.get("is_core", True):
            continue
        status = mp["status"]
        slug   = mp["marketplace"]
        fresh  = mp["freshness_hours"]

        if status == "STALE":
            alerts.append({
                "type":        "MARKETPLACE_STALE",
                "marketplace": slug,
                "severity":    "YELLOW",
                "message":     f"{slug.title()} stale {fresh:.0f}h — last poll {fresh:.0f}h ago",
                "remediation": mp["remediation"],
            })
        elif status == "BLOCKED":
            alerts.append({
                "type":        "MARKETPLACE_BLOCKED",
                "marketplace": slug,
                "severity":    "RED",
                "message":     f"{slug.title()} blocked — {mp['total_failures']} consecutive failures",
                "remediation": mp["remediation"],
            })
        elif status == "NEEDS_MARKETPLACE_URL":
            alerts.append({
                "type":        "NEEDS_URL",
                "marketplace": slug,
                "severity":    "RED",
                "message":     f"{slug.title()} needs URL — no external ID available",
                "remediation": mp["remediation"],
            })
        elif status == "AUTOMATED_RESOLUTION_FAILED":
            alerts.append({
                "type":        "RESOLUTION_FAILED",
                "marketplace": slug,
                "severity":    "RED",
                "message":     f"{slug.title()} automated resolution failed — manual URL required",
                "remediation": mp["remediation"],
            })
        elif status == "ID_RESOLVED_PENDING_POLL":
            alerts.append({
                "type":        "MARKETPLACE_PENDING",
                "marketplace": slug,
                "severity":    "YELLOW",
                "message":     f"{slug.title()} pending first poll — ID resolved, no data yet",
                "remediation": mp["remediation"],
            })

    # Coverage alert
    if total > 0:
        coverage_pct = populated / total * 100
        if coverage_pct < 50:
            alerts.append({
                "type":        "LOW_COVERAGE",
                "marketplace": None,
                "severity":    "RED",
                "message":     f"Coverage only {coverage_pct:.0f}% ({populated}/{total} marketplaces populated)",
                "remediation": "Add marketplace URLs or investigate collector failures.",
            })
        elif coverage_pct < 80:
            alerts.append({
                "type":        "LOW_COVERAGE",
                "marketplace": None,
                "severity":    "YELLOW",
                "message":     f"Coverage {coverage_pct:.0f}% ({populated}/{total} marketplaces populated)",
                "remediation": "Some marketplaces missing — check health for details.",
            })

    return {
        "event_id":  event_id,
        "generated_at": now_utc.isoformat(),
        "alert_count": len(alerts),
        "has_critical": any(a["severity"] == "RED" for a in alerts),
        "alerts": alerts,
        "health_summary": health["summary"],
    }
