from __future__ import annotations

import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def _isolated_bridge_db(monkeypatch):
    """Every bridge test gets its own throwaway SQLite file — never the
    real .bridge_data/bridge.db, and never shared across tests."""
    import app.data.program_rate_rules  # noqa: F401 — circular-import warm-up
    from app.bridge.config import reset_bridge_settings_cache
    from app.bridge.persistence import reset_persistence_cache

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)  # let SQLAlchemy create it fresh
    monkeypatch.setenv("BRIDGE_DB_PATH", path)
    reset_bridge_settings_cache()
    reset_persistence_cache()
    yield path
    reset_bridge_settings_cache()
    reset_persistence_cache()
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def clean_requirements_registry():
    """For tests that call accept_profile() — removes any slug the test
    registers, restoring program_requirements._REGISTRY exactly, since
    that registry is a real module-level global shared across the whole
    test session."""
    from app.data.program_requirements import _REGISTRY
    before = set(_REGISTRY.keys())
    yield
    added = set(_REGISTRY.keys()) - before
    for slug in added:
        del _REGISTRY[slug]
