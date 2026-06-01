"""
Railway container entrypoint (PID 1).

Minimal approach:
  1. Normalise DATABASE_URL
  2. Run alembic migrations as subprocess
  3. os.execv → replace PID-1 with uvicorn so its stdout/stderr are PID-1's

With os.execv, uvicorn IS PID-1 and all its output (including import errors
and TRACE-* startup logs from app.main) flows directly to Railway's log
capture.  The brief re-subscription race is not a concern for import errors
because they happen during uvicorn startup, well after Railway has attached.
"""
import os
import subprocess
import sys


def _stderr(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


_stderr(f"[entrypoint] starting — pid={os.getpid()}")

# ── 1. Normalise DATABASE_URL ─────────────────────────────────────────────────
db_url = os.environ.get("DATABASE_URL", "")
if db_url:
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if "postgresql://" in db_url and "postgresql+asyncpg://" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    os.environ["DATABASE_URL"] = db_url

# ── 2. Run alembic migrations ─────────────────────────────────────────────────
result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    env=os.environ,
    cwd="/app",
)
if result.returncode != 0:
    sys.exit(result.returncode)

# ── 3. exec uvicorn as PID-1 ─────────────────────────────────────────────────
# os.execv replaces this process with uvicorn.  All uvicorn output (including
# TRACE-* logs from app.main, any ImportError, lifespan errors) goes directly
# to the container stdout/stderr that Railway captures.
port = os.environ.get("PORT", "8000")
_stderr(f"[entrypoint] exec uvicorn on port {port}")
os.execv(
    sys.executable,
    [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0",
        "--port", port,
        "--log-level", "info",
    ],
)
