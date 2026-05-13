from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import events, venues, analytics, listings, poll, debug as debug_routes

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    return {"status": "ok", "app": settings.app_name}
