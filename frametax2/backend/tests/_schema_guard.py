"""Fail-closed schema guard for the DB-backed test session.

Root cause it closes (2026-10-01): the suite had NO schema bootstrap. Every DB-backed
test connects through ``app.core.config.settings.DATABASE_URL`` whose default is the
shared ``frametax2`` database, and nothing verified that database had the Alembic
migrations the models require. ``frametax2`` sat at revision 0074 while the models (and
migration 0078, ``budget_documents.source_incentive_estimates``) were at head, so every
test that loaded a ``BudgetDocument`` failed with an UndefinedColumn error that looked
like an unrelated test failure -- and other tests silently ran against an outdated
schema. The isolated acceptance database was already migrated to head; the defect was
that nothing tied a test session to a database at head.

The canonical owner of schema is Alembic (``alembic/versions``); the guard compares the
connected database's ``alembic_version`` with the migration scripts' head and aborts the
session with the exact remediation, rather than patching individual tests. It never
migrates or writes anything.
"""
from __future__ import annotations

import os
from pathlib import Path

#: Optional exact database name the session must be connected to (PROJECT_RULES long-running
#: process rule 9). When set, a mismatch aborts before any query.
EXPECTED_DB_ENV = "CINEGLOBE_TEST_DB_NAME"


def migration_head(backend_dir: Path | None = None) -> str:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    root = backend_dir or Path(__file__).resolve().parents[1]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    heads = ScriptDirectory.from_config(cfg).get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"alembic must have exactly one head, found {heads}")
    return heads[0]


def check_schema(db_name: str, db_revision: str | None, head: str, expected_name: str | None) -> str | None:
    """Pure decision: returns an abort message, or None when the session may proceed."""
    if expected_name and db_name != expected_name:
        return (
            f"test database is {db_name!r} but {EXPECTED_DB_ENV}={expected_name!r}; "
            "refusing to run DB-backed tests against an unintended database."
        )
    if db_revision != head:
        return (
            f"test database {db_name!r} is at Alembic revision {db_revision!r} but the models "
            f"require head {head!r}. Tests would run against an outdated schema (for example "
            "budget_documents.source_incentive_estimates, migration 0078). Point DATABASE_URL at "
            "an isolated, migrated database, or migrate an isolated database with "
            "`alembic upgrade head` -- never the shared frametax2 database."
        )
    return None


def abort_message_for_configured_database() -> str | None:
    """Connects to settings.DATABASE_URL (read-only: one SELECT) and returns an abort message.
    An unreachable database is not a schema finding -- pure-unit sessions still run, and any
    DB-backed test fails on its own connection error."""
    import sqlalchemy as sa

    from app.core.config import settings

    url = sa.engine.make_url(settings.DATABASE_URL)
    engine = sa.create_engine(url, connect_args={"connect_timeout": 5})
    try:
        with engine.connect() as conn:
            try:
                revision = conn.execute(sa.text("select version_num from alembic_version")).scalar()
            except sa.exc.ProgrammingError:
                revision = None
    except sa.exc.OperationalError:
        return None
    finally:
        engine.dispose()
    return check_schema(url.database or "", revision, migration_head(), os.environ.get(EXPECTED_DB_ENV))
