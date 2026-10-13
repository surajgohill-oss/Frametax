"""Session-level test configuration.

The suite's DB-backed tests have no schema bootstrap of their own: they use whatever
database ``DATABASE_URL`` names. This session start refuses to run against a database
whose Alembic revision is not the migration head, so no test can silently use an
outdated schema (see tests/_schema_guard.py for the root cause).
"""
from __future__ import annotations

import pytest

from tests._schema_guard import abort_message_for_configured_database, select_test_database

# Must run before any `app` import reads settings: default to the isolated pytest database.
select_test_database()


def pytest_sessionstart(session):  # noqa: ARG001
    message = abort_message_for_configured_database()
    if message:
        pytest.exit(f"TEST DATABASE SCHEMA GUARD: {message}", returncode=3)


# ── Real-production write guard (NA-RECONCILIATION-11) ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Several older test files evaluate the four REAL anchor productions and one of them DELETES a production's stored facts. PROJECT_RULES forbids that without per-run authorization. This guard makes the rule
# mechanical for every test, whatever session it opens: any INSERT / UPDATE / DELETE whose SQL or parameters name an anchor project id is refused, on whichever database is configured, unless the run is explicitly
# authorized with CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS=<comma-separated anchor ids>. Reads are untouched. Such a test now stops with RealProjectWriteRefused instead of silently mutating a production.
import os as _os


def pytest_configure(config):  # noqa: ARG001
    from sqlalchemy import event

    from app.db.session import engine
    from tests.isolated_records import REAL_ANCHOR_PROJECT_IDS, RealProjectWriteRefused

    authorized = {x.strip().lower() for x in _os.environ.get("CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS", "").split(",") if x.strip()}
    protected = {pid.lower() for pid in REAL_ANCHOR_PROJECT_IDS} - authorized

    def refuse(conn, cursor, statement, parameters, context, executemany):  # noqa: ARG001
        if not protected or not statement.lstrip()[:7].upper().startswith(("INSERT", "UPDATE", "DELETE")):
            return
        blob = f"{statement} {parameters}".lower()
        for pid in protected:
            if pid in blob:
                raise RealProjectWriteRefused(f"refused a write naming the real production {pid} (authorize the run explicitly with CINEGLOBE_AUTHORIZED_REAL_PROJECT_TESTS): {statement[:100]}")

    event.listen(engine.sync_engine, "before_cursor_execute", refuse)
