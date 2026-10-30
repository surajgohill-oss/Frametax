import test from "node:test";
import assert from "node:assert/strict";
import { awaitEvaluation } from "../src/lib/evaluationJob.js";
import { createEvaluationRunStore, RUN_COMPLETED, RUN_FAILED, RUN_RUNNING } from "../src/lib/evaluationRunStore.js";

const NOW = 1_000_000;
const job = (status, extra = {}) => ({ status, project_id: "p1", deadline_seconds: 720, started_at: NOW / 1000, deadline_at: NOW / 1000 + 720, message: null, result_status: null, blockers: [], ...extra });
const opts = { intervalMs: 0, sleep: async () => {}, now: () => NOW };
const seq = (...items) => async () => { const v = items.shift(); if (v instanceof Error) throw v; return v; };

test("polls the real status until the run completes and reports the served result status", async () => {
  const polls = [];
  const status = async () => { polls.push(1); return polls.length < 3 ? job("running") : job("completed", { result_status: "EVALUATION_COMPLETE" }); };
  const out = await awaitEvaluation(async () => job("running"), status, "p1", opts);
  assert.equal(polls.length, 3);
  assert.deepEqual([out.status, out.jobStatus], ["EVALUATION_COMPLETE", "completed"]);
});

test("a server-side timeout is reported with the server's own text, as failed; a retry then completes", async () => {
  const msg = "The evaluation reached its 720 s limit and was stopped. Nothing was half-saved: your inputs are saved and the previous results are kept. Retry when ready.";
  const begins = [job("running"), job("running")];
  const statuses = [job("timed_out", { message: msg }), job("completed", { result_status: "EVALUATION_COMPLETE" })];
  const store = createEvaluationRunStore((id) => awaitEvaluation(async () => begins.shift(), async () => statuses.shift(), id, opts));
  await store.run("p1");
  assert.equal(store.get("p1").status, RUN_FAILED);
  assert.equal(store.get("p1").message, msg);
  await store.run("p1");
  assert.equal(store.get("p1").status, RUN_COMPLETED);
});

test("a failed run and a blocked run surface their reasons; the store keeps one run per project while polling", async () => {
  const a = createEvaluationRunStore((id) => awaitEvaluation(async () => job("running"), async () => job("failed", { message: "rolled back" }), id, opts));
  await a.run("p1");
  assert.deepEqual([a.get("p1").status, a.get("p1").message], [RUN_FAILED, "rolled back"]);
  const b = createEvaluationRunStore((id) => awaitEvaluation(async () => job("running"), async () => job("blocked", { message: "Budget has no lines" }), id, opts));
  await b.run("p1");
  assert.deepEqual([b.get("p1").status, b.get("p1").message], [RUN_FAILED, "Budget has no lines"]);
  let begins = 0;
  let release;
  const gate = new Promise((r) => { release = r; });
  const c = createEvaluationRunStore((id) => { begins += 1; return awaitEvaluation(async () => job("running"), async () => { await gate; return job("completed"); }, id, opts); });
  const r1 = c.run("p1"); const r2 = c.run("p1");
  assert.equal(r1, r2); assert.equal(c.get("p1").status, RUN_RUNNING); assert.equal(begins, 1);
  release(); await r1;
  assert.equal(c.get("p1").status, RUN_COMPLETED);
});

test("a joined run (a second tab) is polled like the first; status errors are tolerated twice, fail on the third", async () => {
  const ok = await awaitEvaluation(async () => ({ ...job("running"), joined: true }), seq(new Error("net"), new Error("net"), job("completed")), "p1", opts);
  assert.equal(ok.jobStatus, "completed");
  await assert.rejects(awaitEvaluation(async () => job("running"), seq(new Error("a"), new Error("b"), new Error("c")), "p1", opts), /Lost contact/);
});

test("a restarted server (idle after running) and a run that never reports by its deadline are failures with a retry message, never an endless spinner", async () => {
  await assert.rejects(awaitEvaluation(async () => job("running"), async () => job("idle"), "p1", opts), /restarted.*Retry/);
  await assert.rejects(awaitEvaluation(async () => job("running"), async () => job("running"), "p1", { ...opts, now: () => NOW + 720_000 + 61_000 }), /deadline/);
});

test("the legacy in-transaction shape (no job) is returned unchanged", async () => {
  const served = { status: "EVALUATION_COMPLETE", ranking: [] };
  assert.equal(await awaitEvaluation(async () => served, async () => { throw new Error("must not poll"); }, "p1", opts), served);
});
