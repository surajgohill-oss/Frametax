import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.api.routes import events, venues, analytics, listings, poll, debug as debug_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)
settings = get_settings()


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
    async with AsyncSessionLocal() as db:
        for table, column in _REQUIRED_COLUMNS:
            row = await db.execute(
                text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = :t AND column_name = :c"
                ),
                {"t": table, "c": column},
            )
            if not row.scalar_one_or_none():
                raise RuntimeError(
                    f"SCHEMA ASSERTION FAILED: {table}.{column} is missing. "
                    "Run 'alembic upgrade head' and restart."
                )
    logger.info("Schema assertion passed — all required columns present")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _assert_schema()
    from app.scheduler import start_scheduler
    await start_scheduler()
    yield
    from app.scheduler import stop_scheduler
    await stop_scheduler()


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
