#!/bin/bash
set -e

# Railway provides DATABASE_URL as postgresql:// but asyncpg requires postgresql+asyncpg://
if [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|postgresql://|postgresql+asyncpg://|g')
fi

echo "[start.sh] Running alembic migrations..."
alembic upgrade head

echo "[start.sh] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
