#!/bin/bash
set -e

echo "[start.sh] Running alembic migrations..."
alembic upgrade head

echo "[start.sh] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
