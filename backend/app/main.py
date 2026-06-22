import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── TRACE 0: module import started ────────────────────────────────────────────
logger.info("TRACE-0: app.main module import started")

from app.config import get_settings
from app.database import AsyncSessionLocal

logger.info("TRACE-1: config + database imported OK")

from app.api.routes import events, venues, analytics, listings, poll, debug as debug_routes, hydrate as hydrate_routes, health as health_routes, intelligence as intelligence_routes, data_health as data_health_routes, gap_monitor as gap_monitor_routes, market_intelligence as market_intelligence_routes, collection_health as collection_health_routes, follows as follows_routes, artist_intelligence as artist_intelligence_routes, reliability as reliability_routes, collect as collect_routes

logger.info("TRACE-2: all route modules imported OK")

settings = get_settings()
logger.info("TRACE-3: settings loaded OK — db_url_prefix=%s", settings.database_url[:30] if settings.database_url else "NONE")


_REQUIRED_COLUMNS = [
    # Core collection
    ("events",                "status"),
    ("events",                "starting_inventory"),
    ("events",                "first_snapshot_at"),
    ("listings",              "extra"),
    ("listings",              "fees"),
    ("listings",              "all_in_price"),
    ("listings",              "market_segment"),
    ("listing_snapshots",     "fees"),
    ("listing_snapshots",     "all_in_price"),
    ("listing_snapshots",     "market_segment"),
    ("tracked_events",        "resolution_source"),
    ("tracked_events",        "lifecycle_phase"),
    # Intelligence layer (Phase 1-3)
    ("event_outcomes",        "postshow_clearance_rate"),
    ("event_outcomes",        "seller_pressure_score"),
    ("artist_market_profiles","avg_clearance_rate"),
    ("event_type_benchmarks", "p50_clearance_rate"),
    ("market_intelligence",   "relisting_rate"),
    # Reliability
    ("scheduler_heartbeats",  "beat_at"),
]


async def _assert_schema() -> None:
    logger.info("TRACE-5a: _assert_schema() entered")
    missing = []
    try:
        async with AsyncSessionLocal() as db:
            logger.info("TRACE-5b: DB session opened for schema check")
            for table, column in _REQUIRED_COLUMNS:
                row = await db.execute(
                    text(
                        "SELECT 1 FROM information_schema.columns "
                        "WHERE table_name = :t AND column_name = :c"
                    ),
                    {"t": table, "c": column},
                )
                if not row.scalar_one_or_none():
                    missing.append(f"{table}.{column}")
    except Exception as exc:
        logger.error("TRACE-5err: schema assertion DB query failed: %s", exc)
        return
    if missing:
        logger.warning(
            "TRACE-5c: SCHEMA MISSING %d column(s): %s",
            len(missing),
            ", ".join(missing),
        )
    else:
        logger.info("TRACE-5c: schema assertion passed — all required columns present")


async def _backfill_starting_inventory() -> None:
    """Backfill events.starting_inventory and first_snapshot_at from listing_snapshots.
    Runs at startup after migration; safe to run multiple times (WHERE IS NULL guard).
    """
    try:
        async with AsyncSessionLocal() as db:
            # first_snapshot_at: MIN(snapshot_at) per event
            r1 = await db.execute(text("""
                UPDATE events e
                SET first_snapshot_at = sub.first_snap
                FROM (
                    SELECT event_id, MIN(snapshot_at) AS first_snap
                    FROM listing_snapshots
                    GROUP BY event_id
                ) sub
                WHERE e.id = sub.event_id
                  AND e.first_snapshot_at IS NULL
            """))
            await db.commit()
            updated_dates = r1.rowcount

            # starting_inventory: count distinct listing_id at the first snapshot time
            r2 = await db.execute(text("""
                UPDATE events e
                SET starting_inventory = sub.cnt
                FROM (
                    SELECT ls.event_id, COUNT(DISTINCT ls.listing_id) AS cnt
                    FROM listing_snapshots ls
                    INNER JOIN (
                        SELECT event_id, MIN(snapshot_at) AS first_snap
                        FROM listing_snapshots
                        GROUP BY event_id
                    ) fs ON fs.event_id = ls.event_id
                       AND ls.snapshot_at = fs.first_snap
                    GROUP BY ls.event_id
                ) sub
                WHERE e.id = sub.event_id
                  AND e.starting_inventory IS NULL
            """))
            await db.commit()
            updated_inv = r2.rowcount

        logger.info(
            "STARTUP_BACKFILL: first_snapshot_at updated=%d, starting_inventory updated=%d",
            updated_dates, updated_inv,
        )
    except Exception as exc:
        logger.error("STARTUP_BACKFILL: failed — %s", exc)


async def _cleanup_zombie_poll_runs() -> None:
    """Mark poll_runs stuck in 'running' for >10 minutes as 'error' on startup."""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text(
                    "UPDATE poll_runs SET status='error', "
                    "error_message='Cleaned up by startup — process restarted while poll was running', "
                    "completed_at=NOW() "
                    "WHERE status='running' AND started_at < NOW() - INTERVAL '10 minutes' "
                    "RETURNING id"
                )
            )
            cleaned = len(result.fetchall())
            await db.commit()
        if cleaned:
            logger.warning(
                "STARTUP_CLEANUP: marked %d zombie poll_run(s) as error "
                "(were stuck in 'running' before restart)",
                cleaned,
            )
        else:
            logger.info("STARTUP_CLEANUP: no zombie poll_runs found")
    except Exception as exc:
        logger.error("STARTUP_CLEANUP: zombie cleanup failed — %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TRACE-4: lifespan() entered")

    logger.info("TRACE-5: calling _assert_schema()")
    await _assert_schema()
    logger.info("TRACE-6: _assert_schema() done")

    logger.info("TRACE-6b: cleaning up zombie poll_runs from prior process")
    await _cleanup_zombie_poll_runs()

    logger.info("TRACE-6c: backfilling starting_inventory from listing_snapshots")
    await _backfill_starting_inventory()

    logger.info("TRACE-7: importing start_scheduler")
    try:
        from app.scheduler import start_scheduler
        logger.info("TRACE-8: start_scheduler imported OK")
    except Exception as exc:
        logger.error("TRACE-8err: failed to import start_scheduler: %s", exc, exc_info=True)
        raise

    logger.info("TRACE-9: calling start_scheduler()")
    try:
        await start_scheduler()
        logger.info("TRACE-10: start_scheduler() done")
    except Exception as exc:
        logger.error("TRACE-10err: start_scheduler() raised: %s", exc, exc_info=True)
        raise

    logger.info("TRACE-11: yielding — server should now accept requests")
    yield

    from app.scheduler import stop_scheduler
    await stop_scheduler()


logger.info("TRACE-3b: building FastAPI app")
app = FastAPI(
    title="LA Concert Watchlist Tracker",
    description="Secondary market ticket intelligence — LA venues",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api")
app.include_router(venues.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(listings.router, prefix="/api")
app.include_router(poll.router, prefix="/api")
app.include_router(debug_routes.router, prefix="/api")
app.include_router(hydrate_routes.router, prefix="/api")
app.include_router(health_routes.router, prefix="/api")
app.include_router(intelligence_routes.router, prefix="/api")
app.include_router(data_health_routes.router, prefix="/api")
app.include_router(gap_monitor_routes.router, prefix="/api")
app.include_router(market_intelligence_routes.router, prefix="/api")
app.include_router(collection_health_routes.router, prefix="/api")
app.include_router(follows_routes.router, prefix="/api")
app.include_router(artist_intelligence_routes.router, prefix="/api")
app.include_router(reliability_routes.router, prefix="/api")
app.include_router(collect_routes.router, prefix="/api")

logger.info("TRACE-3c: app.main module fully loaded — routers registered")


@app.get("/api/health")
async def health():
    import os
    t0 = time.monotonic()
    commit = (
        os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or os.environ.get("GIT_COMMIT")
        or "unknown"
    )
    commit = commit[:12]  # short hash
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
            migration_row = await db.execute(text("SELECT version_num FROM alembic_version"))
            migration = (migration_row.scalar_one_or_none() or "unknown")
        db_ms = round((time.monotonic() - t0) * 1000)
        return {
            "status": "ok",
            "app": settings.app_name,
            "db": "ok",
            "db_ms": db_ms,
            "commit": commit,
            "migration": migration,
        }
    except Exception as exc:
        logger.error("Health check DB ping failed: %s", exc)
        return {
            "status": "degraded",
            "app": settings.app_name,
            "db": "error",
            "error": str(exc),
            "commit": commit,
        }
