"""Session-level test configuration.

The suite's DB-backed tests have no schema bootstrap of their own: they use whatever
database ``DATABASE_URL`` names. This session start refuses to run against a database
whose Alembic revision is not the migration head, so no test can silently use an
outdated schema (see tests/_schema_guard.py for the root cause).
"""
from __future__ import annotations

import pytest

from tests._schema_guard import abort_message_for_configured_database


def pytest_sessionstart(session):  # noqa: ARG001
    message = abort_message_for_configured_database()
    if message:
        pytest.exit(f"TEST DATABASE SCHEMA GUARD: {message}", returncode=3)
