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

from app.api.routes import events, venues, analytics, listings, poll, debug as debug_routes, hydrate as hydrate_routes, health as health_routes, intelligence as intelligence_routes, data_health as data_health_routes, gap_monitor as gap_monitor_routes

logger.info("TRACE-2: all route modules imported OK")

settings = get_settings()
logger.info("TRACE-3: settings loaded OK — db_url_prefix=%s", settings.database_url[:30] if settings.database_url else "NONE")


_REQUIRED_COLUMNS = [
    ("events",            "status"),
    ("listings",          "extra"),
    ("listings",          "fees"),
    ("listings",          "all_in_price"),
    ("listings",          "market_segment"),
    ("listing_snapshots", "fees"),
    ("listing_snapshots", "all_in_price"),
    ("listing_snapshots", "market_segment"),
    ("tracked_events",    "resolution_source"),
    ("tracked_events",    "lifecycle_phase"),
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TRACE-4: lifespan() entered")

    logger.info("TRACE-5: calling _assert_schema()")
    await _assert_schema()
    logger.info("TRACE-6: _assert_schema() done")

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

logger.info("TRACE-3c: app.main module fully loaded — routers registered")


@app.get("/api/health")
async def health():
    t0 = time.monotonic()
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        db_ms = round((time.monotonic() - t0) * 1000)
        return {"status": "ok", "app": settings.app_name, "db": "ok", "db_ms": db_ms}
    except Exception as exc:
        logger.error("Health check DB ping failed: %s", exc)
        return {"status": "degraded", "app": settings.app_name, "db": "error", "error": str(exc)}
