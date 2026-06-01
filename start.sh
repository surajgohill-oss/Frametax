#!/bin/bash
set -e

# Railway provides DATABASE_URL as postgresql:// but asyncpg requires postgresql+asyncpg://
if [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|postgresql://|postgresql+asyncpg://|g')
fi

echo "[start.sh] Running alembic migrations..."
# If the DB is at a revision our migration files don't know about (applied from
# a different branch), stamp our head so alembic recognises the current state,
# then upgrade (no-op) so any future migrations apply cleanly.
set +e
alembic upgrade head 2>&1
ALEMBIC_EXIT=$?
set -e
if [ $ALEMBIC_EXIT -ne 0 ]; then
    echo "[start.sh] alembic upgrade failed (exit $ALEMBIC_EXIT) — DB revision ahead of local files. Stamping head and retrying."
    alembic stamp head
    alembic upgrade head
fi

echo "[start.sh] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
