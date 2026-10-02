"""Create (if missing) and migrate the ISOLATED pytest database to Alembic head.

The DB-backed test workflow must never point at the shared ``frametax2`` database (it sat at an
old Alembic revision and holds real project data). tests/conftest.py defaults the session to
``frametax2_pytest`` and fails closed unless that database is at the migration head; this
script is the one supported way to make it so. It only ever touches a database whose name
matches ``frametax2_pytest*`` and never drops anything.

    python scripts/prepare_test_database.py            # frametax2_pytest on localhost
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import sqlalchemy as sa

DEFAULT_NAME = "frametax2_pytest"
SAFE_NAME = re.compile(r"^frametax2_pytest[a-z0-9_]*$")
ADMIN_URL = "postgresql+psycopg://frametax:frametax@localhost:5432/postgres"
TEST_URL_TEMPLATE = "postgresql+psycopg://frametax:frametax@localhost:5432/{name}"


def main() -> int:
    name = os.environ.get("CINEGLOBE_TEST_DB_NAME", DEFAULT_NAME)
    if not SAFE_NAME.match(name):
        print(f"refusing: {name!r} is not an isolated pytest database name (frametax2_pytest*)")
        return 2
    admin = sa.create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(sa.text("select 1 from pg_database where datname = :n"), {"n": name}).scalar()
        if not exists:
            conn.execute(sa.text(f'create database "{name}"'))
            print(f"created database {name}")
    admin.dispose()
    env = dict(os.environ, DATABASE_URL=TEST_URL_TEMPLATE.format(name=name))
    backend = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend, env=env, check=True)
    print(f"{name} is at Alembic head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
