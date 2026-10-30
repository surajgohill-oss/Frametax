"""Single-flight, deadline-enforced runs of the producer-input evaluation (POST /projects/{id}/evaluation/begin).

The evaluation is the one existing ``evaluate_project`` under the existing bounded workflow (services/evaluation_worker.py ->
bounded_regeneration.regenerate_project, hard 720 s ceiling). This registry only (a) starts it in a child process so the API stays responsive, (b) allows one run
per project -- a second request joins the running one, never duplicates it, (c) enforces the deadline from the parent as well (terminate, then kill; PostgreSQL rolls the
child's transaction back), and (d) reports honest status: running / completed / blocked / timed_out / failed with the start time, the deadline and the elapsed time.

State is per API process. Across processes the worker's advisory lock refuses a duplicate. Nothing here touches stored inputs or generations. Not a fingerprint-hashed module."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.services.bounded_regeneration import HARD_TIMEOUT_SECONDS

log = logging.getLogger(__name__)
KILL_GRACE_S = 20.0
BACKEND_DIR = Path(__file__).resolve().parents[2]

RUNNING, COMPLETED, BLOCKED, TIMED_OUT, FAILED, IDLE = "running", "completed", "blocked", "timed_out", "failed", "idle"

TIMEOUT_MESSAGE = ("The evaluation reached its {limit} s limit and was stopped. Nothing was half-saved: your inputs are saved and the previous results are kept. Retry when ready.")


@dataclass
class EvaluationJob:
    project_id: uuid.UUID
    deadline_s: float
    started_at: float = field(default_factory=time.time)
    status: str = RUNNING
    message: str | None = None
    result_status: str | None = None
    blockers: list = field(default_factory=list)
    finished_at: float | None = None
    joined: int = 0
    task: asyncio.Task | None = field(default=None, repr=False)

    def snapshot(self, *, joined: bool = False) -> dict:
        now = self.finished_at or time.time()
        return {"status": self.status, "project_id": str(self.project_id), "deadline_seconds": self.deadline_s,
                "started_at": self.started_at, "deadline_at": self.started_at + self.deadline_s, "elapsed_seconds": round(now - self.started_at, 1),
                "finished_at": self.finished_at, "message": self.message, "result_status": self.result_status, "blockers": self.blockers, "joined": joined}


def worker_command(project_id: uuid.UUID, deadline_s: float) -> list[str]:
    return [sys.executable, "-m", "app.services.evaluation_worker", str(project_id), "--timeout", str(deadline_s)]


class EvaluationJobs:
    def __init__(self, *, deadline_s: float = HARD_TIMEOUT_SECONDS, command=worker_command, grace_s: float = KILL_GRACE_S):
        self.deadline_s, self._command, self._grace_s = min(deadline_s, HARD_TIMEOUT_SECONDS), command, grace_s
        self._jobs: dict[uuid.UUID, EvaluationJob] = {}

    def status(self, project_id: uuid.UUID) -> dict:
        job = self._jobs.get(project_id)
        return job.snapshot() if job else {"status": IDLE, "project_id": str(project_id), "deadline_seconds": self.deadline_s}

    def start(self, project_id: uuid.UUID) -> dict:
        """Start the evaluation, or join the one already running. Returns the status snapshot immediately."""
        job = self._jobs.get(project_id)
        if job is not None and job.status == RUNNING:
            job.joined += 1
            return job.snapshot(joined=True)
        job = EvaluationJob(project_id=project_id, deadline_s=self.deadline_s)
        self._jobs[project_id] = job
        job.task = asyncio.ensure_future(self._run(job))
        return job.snapshot()

    async def wait(self, project_id: uuid.UUID) -> dict:
        job = self._jobs.get(project_id)
        if job is not None and job.task is not None:
            await asyncio.shield(job.task)
        return self.status(project_id)

    async def _run(self, job: EvaluationJob) -> None:
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(*self._command(job.project_id, job.deadline_s), cwd=str(BACKEND_DIR),
                                                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            try:
                out, err = await asyncio.wait_for(proc.communicate(), timeout=job.deadline_s + self._grace_s)
            except asyncio.TimeoutError:
                await self._stop(proc)
                return self._finish(job, TIMED_OUT, TIMEOUT_MESSAGE.format(limit=int(job.deadline_s)))
            self._interpret(job, proc.returncode, out.decode(errors="replace"), err.decode(errors="replace"))
        except asyncio.CancelledError:
            if proc is not None:
                await self._stop(proc)
            self._finish(job, FAILED, "The evaluation was cancelled because the server is shutting down. Your inputs are saved; retry.")
            raise
        except Exception as exc:  # noqa: BLE001
            self._finish(job, FAILED, f"The evaluation could not be started: {type(exc).__name__}. Your inputs are saved; retry.")

    async def _stop(self, proc) -> None:
        if proc.returncode is not None:
            return
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=self._grace_s / 2)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()

    def _interpret(self, job: EvaluationJob, code: int, out: str, err: str) -> None:
        lines = [l for l in out.strip().splitlines() if l.startswith("{")]
        try:
            result = json.loads(lines[-1]) if lines else {}
        except ValueError:
            result = {}
        outcome = result.get("outcome")
        if outcome == "COMPLETED":
            job.result_status, job.blockers = result.get("status"), list(result.get("blockers") or [])
            if job.blockers or (job.result_status or "").startswith(("BLOCKED", "BUDGET_REQUIRED")):
                return self._finish(job, BLOCKED, (job.blockers or ["Evaluation is blocked on incomplete inputs."])[0])
            return self._finish(job, COMPLETED, None)
        if outcome == "ALREADY_RUNNING":
            return self._finish(job, FAILED, "Another evaluation of this project is already running; wait for it to finish.")
        if outcome == "TIMED_OUT":
            return self._finish(job, TIMED_OUT, TIMEOUT_MESSAGE.format(limit=int(job.deadline_s)))
        if not outcome and time.time() - job.started_at >= job.deadline_s:  # the faulthandler backstop ends the process with no result line
            return self._finish(job, TIMED_OUT, TIMEOUT_MESSAGE.format(limit=int(job.deadline_s)))
        log.warning("evaluation worker for %s ended with code %s and no usable result; stderr tail: %s", job.project_id, code, err.strip()[-600:])
        self._finish(job, FAILED, "The evaluation failed and was rolled back. Your inputs are saved and the previous results are kept. Retry, or contact support if it repeats.")

    @staticmethod
    def _finish(job: EvaluationJob, status: str, message: str | None) -> None:
        job.status, job.message, job.finished_at = status, message, time.time()


def _configured_deadline() -> float:
    """CINEGLOBE_EVALUATION_DEADLINE_SECONDS can only LOWER the deadline (for tests / smaller deployments); it can never raise the 720 s ceiling."""
    try:
        return float(os.environ.get("CINEGLOBE_EVALUATION_DEADLINE_SECONDS", HARD_TIMEOUT_SECONDS))
    except ValueError:
        return HARD_TIMEOUT_SECONDS


_jobs = EvaluationJobs(deadline_s=_configured_deadline())


def get_evaluation_jobs() -> EvaluationJobs:
    return _jobs
