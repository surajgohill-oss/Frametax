"""Cross-API-process duplicate / status behaviour and restart recovery of the producer-input evaluation (FP-ARC-02 residuals).

REAL separate OS processes on the isolated ``frametax2_pytest`` database; no evaluation of any production runs (the "other process" only holds the project's advisory lock, which is
exactly what another API process's worker holds while it evaluates):

* a second process's status reports the run as ``running`` (``external``) with start and deadline, and its Save JOINS it instead of starting a worker;
* when the lock holder ends, status goes back to idle and a Save starts normally;
* a worker whose API process is killed exits at once, its connection closes (the transaction rolls back) and its advisory lock is released (restart recovery).
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine
from app.services.evaluation_jobs import EvaluationJobs, external_run
from app.services.evaluation_worker import advisory_key

BACKEND = Path(__file__).resolve().parents[1]

HOLDER = """
import asyncio, os, sys, uuid
from sqlalchemy import text
from app.db.session import engine
from app.services.evaluation_worker import advisory_key, watch_parent
pid = uuid.UUID(sys.argv[1])
if sys.argv[2] == "watch": watch_parent(os.getppid(), poll_s=0.2)
async def main():
    async with engine.connect() as c:
        assert (await c.execute(text("select pg_try_advisory_lock(:k)"), {"k": advisory_key(pid)})).scalar()
        await c.execute(text("create temp table _open_tx (x int)")); await c.execute(text("insert into _open_tx values (1)"))  # an open transaction, never committed
        print("HELD", flush=True)
        await asyncio.sleep(120)
asyncio.run(main())
"""

PARENT = """
import subprocess, sys
child = subprocess.Popen([sys.executable, "-c", sys.argv[1], sys.argv[2], "watch"], stdout=subprocess.PIPE, text=True)
print("CHILD", child.pid, child.stdout.readline().strip(), flush=True)
import time; time.sleep(120)
"""


def _spawn_holder(pid: uuid.UUID) -> subprocess.Popen:
    proc = subprocess.Popen([sys.executable, "-c", HOLDER, str(pid), "plain"], cwd=BACKEND, stdout=subprocess.PIPE, text=True, env=os.environ.copy())
    assert proc.stdout.readline().strip() == "HELD"
    return proc


async def _external(pid):
    async with AsyncSession(engine) as session:
        return await external_run(session, pid)


async def _eventually(predicate, timeout_s=10.0):
    end = time.monotonic() + timeout_s
    while time.monotonic() < end:
        if await predicate():
            return True
        await asyncio.sleep(0.2)
    return False


@pytest.mark.asyncio
async def test_a_run_held_by_another_process_is_reported_running_and_a_save_joins_it_without_a_worker():
    pid = uuid.uuid4()
    assert await _external(pid) is None
    holder = _spawn_holder(pid)
    try:
        ext = await _external(pid)
        assert ext is not None and ext["status"] == "running" and ext["external"] is True and ext["project_id"] == str(pid)
        assert abs(time.time() - ext["started_at"]) < 60 and ext["deadline_at"] == ext["started_at"] + 720 and ext["elapsed_seconds"] >= 0

        spawned = []
        jobs = EvaluationJobs(command=lambda *a: spawned.append(a) or ["true"])
        assert jobs.status(pid, ext)["status"] == "running" and jobs.status(pid, ext)["external"] is True
        joined = jobs.start(pid, ext)  # a Save in this "second API process"
        assert joined["status"] == "running" and joined["joined"] is True and joined["external"] is True
        assert spawned == [] and not jobs.running_here(pid), "joining another process's run must not start a worker"
        assert jobs.status(uuid.uuid4(), None)["status"] == "idle"
    finally:
        holder.kill()
        holder.wait()
    assert await _eventually(lambda: _is_none(pid)), "the lock must disappear when the holding process ends"
    jobs = EvaluationJobs(command=lambda *a: ["true"])
    assert jobs.status(pid, await _external(pid))["status"] == "idle"
    started = jobs.start(pid, await _external(pid))
    assert started["status"] == "running" and started["joined"] is False and jobs.running_here(pid)  # nothing held it: a normal start
    await jobs.wait(pid)


async def _is_none(pid):
    return await _external(pid) is None


@pytest.mark.asyncio
async def test_a_local_run_takes_precedence_and_other_projects_are_independent():
    held, free = uuid.uuid4(), uuid.uuid4()
    holder = _spawn_holder(held)
    try:
        ext = await _external(held)
        assert ext is not None and await _external(free) is None
        jobs = EvaluationJobs(command=lambda *a: [sys.executable, "-c", "import time; time.sleep(30)"], grace_s=1.0)
        local = jobs.start(free, None)
        assert local["status"] == "running" and "external" not in local
        assert jobs.status(free, ext)["project_id"] == str(free), "a locally running job is reported as itself, not as an external hold"
        assert jobs.status(held, ext)["external"] is True
        for task in [j.task for j in jobs._jobs.values()]:
            task.cancel()
        await asyncio.gather(*[j.task for j in jobs._jobs.values()], return_exceptions=True)
    finally:
        holder.kill()
        holder.wait()


@pytest.mark.asyncio
async def test_killing_the_api_process_makes_its_worker_exit_roll_back_and_release_the_lock():
    pid = uuid.uuid4()
    parent = subprocess.Popen([sys.executable, "-c", PARENT, HOLDER, str(pid)], cwd=BACKEND, stdout=subprocess.PIPE, text=True, env=os.environ.copy())
    try:
        tag, child_pid, held = parent.stdout.readline().split()
        assert (tag, held) == ("CHILD", "HELD")
        assert await _external(pid) is not None, "the worker holds the project while its API process lives"
        parent.kill()  # the API process dies (restart / crash / SIGKILL)
        parent.wait()
        assert await _eventually(lambda: _is_none(pid), 10.0), "the orphaned worker must leave and release the project's lock"
        with pytest.raises(ProcessLookupError):
            for _ in range(50):  # the child is gone (not merely unlocked)
                os.kill(int(child_pid), 0)
                await asyncio.sleep(0.1)
            os.kill(int(child_pid), 0)
            raise AssertionError("worker process still alive")
        async with AsyncSession(engine) as session:
            assert (await session.execute(text("select pg_try_advisory_lock(:k)"), {"k": advisory_key(pid)})).scalar(), "the project can be evaluated again at once"
            await session.execute(text("select pg_advisory_unlock(:k)"), {"k": advisory_key(pid)})
    finally:
        if parent.poll() is None:
            parent.kill()
