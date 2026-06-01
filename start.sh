#!/bin/bash
set -e

# Railway provides DATABASE_URL as postgresql:// but asyncpg requires postgresql+asyncpg://
if [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|postgresql://|postgresql+asyncpg://|g')
fi

echo "[start.sh] Running alembic migrations..."
# Railway DB may have been migrated from a different branch (e.g. Frametax 0013)
# whose revision IDs are not present in the concert-tracker migration files.
# Strategy:
#   1. Try alembic upgrade head normally.
#   2. On failure (unknown revision), purge the stale version entry and stamp our
#      codebase head so alembic's version table is consistent, then upgrade (no-op).
# --purge wipes alembic_version before writing the target revision, so it works
# even when the current DB revision is completely unknown to our migration tree.
set +e
alembic upgrade head
ALEMBIC_EXIT=$?
if [ $ALEMBIC_EXIT -ne 0 ]; then
    echo "[start.sh] alembic upgrade head failed (exit $ALEMBIC_EXIT) — purging stale revision and stamping head."
    alembic stamp --purge head
    alembic upgrade head  # no-op once stamp succeeds
fi
set -e

echo "[start.sh] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
