"""
Railway container entrypoint (PID 1).
Replaces start.sh so everything runs in one Python process before exec'ing uvicorn.
This ensures all startup output uses Python's logging module and appears in Railway logs.
"""
import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-5s [%(name)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("entrypoint")

logger.info("Container starting — python=%s pid=%d", sys.executable, os.getpid())
logger.info("PATH=%s", os.environ.get("PATH", "unset"))

# ── 1. Normalise DATABASE_URL (Railway injects postgresql:// not postgresql+asyncpg://)
db_url = os.environ.get("DATABASE_URL", "")
if db_url:
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if "postgresql://" in db_url and "postgresql+asyncpg://" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    os.environ["DATABASE_URL"] = db_url
    logger.info("DATABASE_URL normalised to asyncpg driver")

# ── 2. Run alembic migrations
logger.info("Running alembic upgrade head …")
alembic_result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    env=os.environ,
)
if alembic_result.returncode != 0:
    logger.error("alembic upgrade head failed (exit %d)", alembic_result.returncode)
    sys.exit(alembic_result.returncode)
logger.info("alembic upgrade head succeeded")

# ── 3. Exec uvicorn (replaces this process — becomes the new PID 1)
port = os.environ.get("PORT", "8000")
logger.info("Launching uvicorn on 0.0.0.0:%s …", port)
sys.stdout.flush()
sys.stderr.flush()
os.execv(
    sys.executable,
    [sys.executable, "-m", "uvicorn", "app.main:app",
     "--host", "0.0.0.0", "--port", port],
)
