"""FP-ARC-02: the producer-input evaluation runs under an enforced deadline, single-flight, with honest status and reliable cleanup.

The jobs registry is exercised with stand-in child commands (no database, no real production); the worker's lock key and the 720 s ceiling are pinned directly."""
from __future__ import annotations

import asyncio
import json
import sys
import time
import uuid

import pytest

from app.services import evaluation_jobs as ej
from app.services.bounded_regeneration import HARD_TIMEOUT_SECONDS
from app.services.evaluation_worker import _evaluate, advisory_key


def child(code: str):
    return lambda project_id, deadline_s: [sys.executable, "-I", "-c", code]


def jobs_with(code: str, deadline_s: float = 5.0, grace_s: float = 1.0) -> ej.EvaluationJobs:
    return ej.EvaluationJobs(deadline_s=deadline_s, command=child(code), grace_s=grace_s)


@pytest.mark.asyncio
async def test_a_completed_run_reports_completed_and_idle_before_any_run():
    pid = uuid.uuid4()
    jobs = jobs_with('import json;print(json.dumps({"outcome":"COMPLETED","status":"EVALUATION_COMPLETE"}))')
    assert jobs.status(pid)["status"] == ej.IDLE
    assert jobs.start(pid)["status"] == ej.RUNNING
    done = await jobs.wait(pid)
    assert done["status"] == ej.COMPLETED and done["result_status"] == "EVALUATION_COMPLETE" and done["message"] is None


@pytest.mark.asyncio
async def test_a_second_request_while_running_joins_the_run_and_never_starts_another(tmp_path):
    marker = tmp_path / "starts.txt"
    code = f'import time;open({str(marker)!r},"a").write("x");time.sleep(1);print(\'{{"outcome":"COMPLETED","status":"EVALUATION_REUSED"}}\')'
    pid, jobs = uuid.uuid4(), jobs_with(code)
    first = jobs.start(pid)
    second, third = jobs.start(pid), jobs.start(pid)
    assert first["joined"] is False and second["joined"] is True and third["joined"] is True
    assert second["started_at"] == first["started_at"]
    assert (await jobs.wait(pid))["status"] == ej.COMPLETED
    assert marker.read_text() == "x", "exactly one child process ran for three requests"
    jobs.start(pid)  # after completion a new request is a genuine retry
    await jobs.wait(pid)
    assert marker.read_text() == "xx"


@pytest.mark.asyncio
async def test_the_parent_deadline_stops_a_hung_child_and_reports_timed_out_then_a_retry_runs():
    pid = uuid.uuid4()
    jobs = jobs_with("import time;time.sleep(60)", deadline_s=1.0, grace_s=1.0)
    started = time.monotonic()
    jobs.start(pid)
    done = await jobs.wait(pid)
    assert done["status"] == ej.TIMED_OUT and "previous results are kept" in done["message"] and "inputs are saved" in done["message"]
    assert time.monotonic() - started < 6, "the hung child was terminated at the deadline plus grace, not left running"
    jobs._command = child('import json;print(json.dumps({"outcome":"COMPLETED","status":"EVALUATION_COMPLETE"}))')
    jobs.deadline_s = 5.0
    jobs.start(pid)
    assert (await jobs.wait(pid))["status"] == ej.COMPLETED, "retry after a timeout starts a fresh run"


@pytest.mark.asyncio
async def test_the_worker_own_timeout_outcome_is_reported_as_timed_out_not_failed():
    pid = uuid.uuid4()
    jobs = jobs_with('import json,sys;print(json.dumps({"outcome":"TIMED_OUT"}));sys.exit(2)')
    jobs.start(pid)
    assert (await jobs.wait(pid))["status"] == ej.TIMED_OUT


@pytest.mark.asyncio
async def test_a_crashing_child_is_failed_with_a_retry_message_and_a_retry_succeeds():
    pid = uuid.uuid4()
    jobs = jobs_with("import sys;sys.exit(1)")
    jobs.start(pid)
    done = await jobs.wait(pid)
    assert done["status"] == ej.FAILED and "rolled back" in done["message"] and "Retry" in done["message"]
    jobs._command = child('import json;print(json.dumps({"outcome":"COMPLETED","status":"EVALUATION_COMPLETE"}))')
    jobs.start(pid)
    assert (await jobs.wait(pid))["status"] == ej.COMPLETED


@pytest.mark.asyncio
async def test_a_worker_killed_from_outside_before_the_deadline_is_failed_not_timed_out():
    pid = uuid.uuid4()
    jobs = jobs_with("import os,signal;os.kill(os.getpid(), signal.SIGKILL)", deadline_s=60)
    jobs.start(pid)
    done = await jobs.wait(pid)
    assert done["status"] == ej.FAILED and "limit" not in done["message"] and done["elapsed_seconds"] < 10


@pytest.mark.asyncio
async def test_blocked_inputs_are_reported_as_blocked_with_the_first_blocker():
    pid = uuid.uuid4()
    jobs = jobs_with('import json;print(json.dumps({"outcome":"COMPLETED","status":"BLOCKED_INCOMPLETE_INPUTS","blockers":["Budget has no lines"]}))')
    jobs.start(pid)
    done = await jobs.wait(pid)
    assert done["status"] == ej.BLOCKED and done["message"] == "Budget has no lines"


@pytest.mark.asyncio
async def test_an_evaluation_already_running_elsewhere_is_refused_not_duplicated():
    pid = uuid.uuid4()
    jobs = jobs_with('import json,sys;print(json.dumps({"outcome":"ALREADY_RUNNING"}));sys.exit(3)')
    jobs.start(pid)
    done = await jobs.wait(pid)
    # Reached only in the instant between the status check and the worker's lock attempt (a held lock is normally joined, see test_evaluation_cross_process.py).
    assert done["status"] == ej.FAILED and "another server process" in done["message"] and "running" in done["message"]


@pytest.mark.asyncio
async def test_cancelling_the_server_task_terminates_the_child(tmp_path):
    pid, jobs = uuid.uuid4(), jobs_with("import time;time.sleep(60)", deadline_s=30, grace_s=2)
    jobs.start(pid)
    await asyncio.sleep(0.5)
    task = jobs._jobs[pid].task
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert jobs.status(pid)["status"] == ej.FAILED


@pytest.mark.asyncio
async def test_runs_of_different_projects_are_independent():
    a, b = uuid.uuid4(), uuid.uuid4()
    jobs = jobs_with("import time;time.sleep(0.5);print('{\"outcome\":\"COMPLETED\",\"status\":\"EVALUATION_COMPLETE\"}')")
    jobs.start(a)
    assert jobs.start(b)["joined"] is False
    assert (await jobs.wait(a))["status"] == (await jobs.wait(b))["status"] == ej.COMPLETED


@pytest.mark.asyncio
async def test_status_while_running_exposes_start_deadline_and_elapsed_and_is_served_without_blocking():
    pid = uuid.uuid4()
    jobs = jobs_with("import time;time.sleep(1.5)", deadline_s=60)
    jobs.start(pid)
    t = time.monotonic()
    snap = jobs.status(pid)
    assert time.monotonic() - t < 0.05
    assert snap["status"] == ej.RUNNING and snap["deadline_at"] == pytest.approx(snap["started_at"] + 60) and snap["elapsed_seconds"] >= 0
    await jobs.wait(pid)


def test_the_720_second_ceiling_is_not_raised_anywhere_on_this_path():
    assert HARD_TIMEOUT_SECONDS == 720
    assert ej.EvaluationJobs(deadline_s=10_000).deadline_s == 720
    assert ej.get_evaluation_jobs().deadline_s == 720
    assert "720" in " ".join(ej.worker_command(uuid.uuid4(), 720)) or "--timeout" in ej.worker_command(uuid.uuid4(), 720)


def test_the_worker_lock_key_is_stable_per_project_signed_64_bit_and_distinct():
    a, b = uuid.uuid4(), uuid.uuid4()
    assert advisory_key(a) == advisory_key(a) != advisory_key(b)
    assert -(2**63) <= advisory_key(a) < 2**63


@pytest.mark.asyncio
async def test_the_worker_refuses_a_second_evaluation_of_a_project_whose_lock_is_held_and_releases_the_lock_when_it_ends():
    from sqlalchemy import text
    from app.db.session import engine

    pid = uuid.uuid4()
    async with engine.connect() as holder:
        assert (await holder.execute(text("select pg_try_advisory_lock(:k)"), {"k": advisory_key(pid)})).scalar()
        assert await _evaluate(pid, 5.0) == {"outcome": "ALREADY_RUNNING"}
        await holder.execute(text("select pg_advisory_unlock(:k)"), {"k": advisory_key(pid)})
    # lock released: the worker now proceeds past the lock (an unknown project is simply not found, nothing is written)
    out = await _evaluate(pid, 30.0)
    assert out["outcome"] == "COMPLETED" and out.get("status") == "PROJECT_NOT_FOUND"
    async with engine.connect() as probe:
        assert (await probe.execute(text("select pg_try_advisory_lock(:k)"), {"k": advisory_key(pid)})).scalar(), "the worker left no lock behind"
        await probe.execute(text("select pg_advisory_unlock(:k)"), {"k": advisory_key(pid)})


def test_the_configured_deadline_can_lower_but_never_raise_the_ceiling(monkeypatch):
    monkeypatch.setenv("CINEGLOBE_EVALUATION_DEADLINE_SECONDS", "25")
    assert ej._configured_deadline() == 25.0
    monkeypatch.setenv("CINEGLOBE_EVALUATION_DEADLINE_SECONDS", "99999")
    assert ej.EvaluationJobs(deadline_s=ej._configured_deadline()).deadline_s == 720
    monkeypatch.setenv("CINEGLOBE_EVALUATION_DEADLINE_SECONDS", "garbage")
    assert ej._configured_deadline() == 720
