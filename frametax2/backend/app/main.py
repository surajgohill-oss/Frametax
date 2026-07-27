"""
FrameTax 2.0 — FastAPI application entry point.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import budgets, cineglobe, documents, incentive_programs, jurisdictions, optimization, projects, structures
from app.bridge.api import router as bridge_router
from app.core.config import settings

app = FastAPI(
    title="FrameTax 2.0 API",
    description=(
        "Deterministic film production incentive analysis engine. "
        "LLMs extract; the engine calculates."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(jurisdictions.router, prefix="/api/v1")
app.include_router(incentive_programs.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(budgets.router, prefix="/api/v1")
app.include_router(structures.router, prefix="/api/v1")
app.include_router(optimization.router, prefix="/api/v1")
app.include_router(cineglobe.router, prefix="/api/v1")
# Cross-Model Bridge — internal development infrastructure. Namespaced
# under /api/v1/bridge, NOT referenced by frontend/src/api.js, NOT
# linked from any producer-facing screen. Same operations as
# app/bridge/cli.py, exposed over HTTP for programmatic/admin use.
app.include_router(bridge_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
