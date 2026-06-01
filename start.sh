#!/bin/bash
set -e

# Ensure pip-installed binaries (/usr/local/bin) are on PATH
export PATH="/usr/local/bin:$PATH"

# Railway provides DATABASE_URL as postgresql:// but asyncpg requires postgresql+asyncpg://
if [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|postgresql://|postgresql+asyncpg://|g')
fi

python3 -c "
import logging, sys, os
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logging.info('[start.sh] Starting — PATH=%s', os.environ.get('PATH', 'unset'))
logging.info('[start.sh] python=%s', sys.executable)
"

python3 -m alembic upgrade head

python3 -c "
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logging.info('[start.sh] alembic done, launching uvicorn...')
"

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
