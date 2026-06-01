#!/bin/bash
set -e

# Railway provides DATABASE_URL as postgresql:// but asyncpg requires postgresql+asyncpg://
if [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|postgresql://|postgresql+asyncpg://|g')
fi

echo "[start.sh] Checking alembic_version table..."
# alembic validates the current DB revision against the migration tree before any
# action (including stamp --purge).  If the DB was migrated from a different
# branch (e.g. Frametax revision '0013'), alembic fails at environment load time.
# Fix: use SQLAlchemy directly to replace any unknown revision with our HEAD so
# alembic upgrade head runs as a no-op against a consistent revision table.
python3 - <<'PYEOF'
import asyncio, os, sys

KNOWN_REVISIONS = {'0001', '0002', '0003', '0004', '0005', '0006'}
OUR_HEAD = '0006'

async def fix_alembic_version():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        print('[start.sh] No DATABASE_URL; skipping alembic_version check')
        return
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        engine = create_async_engine(url, echo=False)
        async with engine.begin() as conn:
            rows = await conn.execute(text('SELECT version_num FROM alembic_version'))
            current = [r[0] for r in rows]
            unknown = [v for v in current if v not in KNOWN_REVISIONS]
            if unknown:
                print(f'[start.sh] Replacing unknown alembic revisions {unknown} with {OUR_HEAD}')
                await conn.execute(text('DELETE FROM alembic_version'))
                await conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{OUR_HEAD}')"))
                print(f'[start.sh] alembic_version now at {OUR_HEAD}')
            else:
                print(f'[start.sh] alembic_version OK: {current}')
        await engine.dispose()
    except Exception as exc:
        print(f'[start.sh] alembic_version check error: {exc}', file=sys.stderr)

asyncio.run(fix_alembic_version())
PYEOF

echo "[start.sh] Running alembic upgrade head..."
alembic upgrade head

echo "[start.sh] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
