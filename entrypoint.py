"""
Railway container entrypoint (PID 1).

Responsibilities:
  1. Normalise DATABASE_URL (postgres:// → postgresql+asyncpg://)
  2. exec uvicorn as PID-1

Alembic migrations are handled by railway.toml preDeployCommand
and must NOT be run here (would duplicate work and slow startup).
"""
import os
import sys


def _log(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


_log(f"[entrypoint] starting — pid={os.getpid()}")

# ── 1. Normalise DATABASE_URL ─────────────────────────────────────────────────
db_url = os.environ.get("DATABASE_URL", "")
if db_url:
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if "postgresql://" in db_url and "postgresql+asyncpg://" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    os.environ["DATABASE_URL"] = db_url
    _log(f"[entrypoint] DATABASE_URL normalised")

# ── 2. exec uvicorn as PID-1 ─────────────────────────────────────────────────
port = os.environ.get("PORT", "8000")
_log(f"[entrypoint] exec uvicorn on port {port}")

try:
    os.execv(
        sys.executable,
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "0.0.0.0",
            "--port", port,
            "--log-level", "info",
        ],
    )
except Exception as exc:
    sys.stdout.write(f"[entrypoint] os.execv FAILED: {exc}\n")
    sys.stdout.flush()
    sys.exit(1)
