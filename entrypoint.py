"""
Railway container entrypoint (PID 1).

Keeps PID 1 alive and runs uvicorn as a child process so that Railway's log
capture sees continuous output from a stable process.  Previously, os.execv()
replaced the PID-1 image with uvicorn and Railway lost the log stream in the
brief re-subscription window, making all uvicorn output (including import
errors) invisible.

Strategy:
  1. Normalise DATABASE_URL
  2. Run alembic as subprocess (same as before)
  3. Run an import smoke-test as subprocess — any ImportError in app.main
     will be printed to stderr and show up in Railway logs
  4. Run uvicorn as subprocess.Popen with SIGTERM/SIGINT forwarding
  5. Wait for uvicorn; exit with its return code
"""
import os
import signal
import subprocess
import sys


def _log(msg: str) -> None:
    """Write directly to stderr with immediate flush (not via logging module)."""
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


_log(f"[entrypoint] Container starting — python={sys.executable} pid={os.getpid()}")

# ── 1. Normalise DATABASE_URL ─────────────────────────────────────────────────
db_url = os.environ.get("DATABASE_URL", "")
if db_url:
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if "postgresql://" in db_url and "postgresql+asyncpg://" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    os.environ["DATABASE_URL"] = db_url
    _log("[entrypoint] DATABASE_URL normalised to asyncpg driver")
else:
    _log("[entrypoint] WARNING: DATABASE_URL not set — using default")

# ── 2. Run alembic migrations ─────────────────────────────────────────────────
_log("[entrypoint] Running alembic upgrade head …")
alembic_result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    env=os.environ,
)
if alembic_result.returncode != 0:
    _log(f"[entrypoint] alembic upgrade head FAILED (exit {alembic_result.returncode})")
    sys.exit(alembic_result.returncode)
_log("[entrypoint] alembic upgrade head succeeded")

# ── 3. Import smoke-test ──────────────────────────────────────────────────────
# Runs app.main in a fresh subprocess. Any ImportError or RuntimeError shows
# up in Railway logs here, before we attempt to start the server.
# app.main's own TRACE-0..TRACE-3c log lines will also appear, giving the
# full module-level import trace.
_log("[entrypoint] Running app.main import smoke-test …")
smoke = subprocess.run(
    [sys.executable, "-c",
     "import sys; sys.exit(0) if __import__('app.main', fromlist=['app']) else sys.exit(1)"],
    env=os.environ,
    cwd="/app",
)
if smoke.returncode != 0:
    _log(f"[entrypoint] SMOKE-TEST FAILED (exit {smoke.returncode}) — import error above")
    sys.exit(1)
_log("[entrypoint] Smoke-test passed — app.main imports cleanly")

# ── 4. Launch uvicorn as subprocess ──────────────────────────────────────────
port = os.environ.get("PORT", "8000")
_log(f"[entrypoint] Launching uvicorn on 0.0.0.0:{port} …")

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app",
     "--host", "0.0.0.0", "--port", port,
     "--log-level", "info"],
    env=os.environ,
    cwd="/app",
)

# Forward SIGTERM / SIGINT so uvicorn shuts down gracefully when Railway
# stops the container (Docker sends SIGTERM to PID 1).
def _forward_signal(sig, _frame):
    _log(f"[entrypoint] Forwarding signal {sig} to uvicorn (pid={proc.pid})")
    try:
        proc.send_signal(sig)
    except ProcessLookupError:
        pass  # uvicorn already exited

signal.signal(signal.SIGTERM, _forward_signal)
signal.signal(signal.SIGINT, _forward_signal)

_log(f"[entrypoint] uvicorn started (pid={proc.pid}), waiting …")
rc = proc.wait()
_log(f"[entrypoint] uvicorn exited with code {rc}")
sys.exit(rc)
