#!/bin/bash
set -e

# Ensure pip-installed binaries (/usr/local/bin) are on PATH
export PATH="/usr/local/bin:$PATH"

# Railway provides DATABASE_URL as postgresql:// but asyncpg requires postgresql+asyncpg://
if [ -n "$DATABASE_URL" ]; then
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|postgresql://|postgresql+asyncpg://|g')
fi

# Diagnostic: output via print() to stdout (PYTHONUNBUFFERED=1 ensures immediate flush)
python3 << 'PYDIAG'
import sys, os
print("[start.sh] DIAGNOSTIC stdout: python ok, pid=", os.getpid(), flush=True)
sys.stderr.write("[start.sh] DIAGNOSTIC stderr: python ok\n")
sys.stderr.flush()
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("startup").info("[start.sh] DIAGNOSTIC logging: python ok, PATH=%s", os.environ.get("PATH",""))
PYDIAG

python3 -m alembic upgrade head

python3 -c "import logging; logging.basicConfig(level=logging.INFO); logging.getLogger('startup').info('[start.sh] alembic done, launching uvicorn')"

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
