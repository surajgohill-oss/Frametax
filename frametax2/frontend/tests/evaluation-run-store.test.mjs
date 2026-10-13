import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createEvaluationRunStore, RUN_COMPLETED, RUN_FAILED, RUN_IDLE, RUN_RUNNING } from "../src/lib/evaluationRunStore.js";

const SRC = join(import.meta.dirname, "..", "src");
const read = (...p) => readFileSync(join(SRC, ...p), "utf8");

function deferred() {
  let resolve, reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

test("the run state is the real operation: idle, then running while the request is in flight, then completed", async () => {
  const d = deferred();
  const store = createEvaluationRunStore(() => d.promise);
  const seen = [];
  store.subscribe(() => seen.push(store.get("p1").status));
  assert.equal(store.get("p1").status, RUN_IDLE);
  const run = store.run("p1");
  assert.equal(store.get("p1").status, RUN_RUNNING);
  assert.equal(store.isRunning("p1"), true);
  d.resolve({ status: "EVALUATION_COMPLETE" });
  await run;
  assert.equal(store.get("p1").status, RUN_COMPLETED);
  assert.deepEqual(seen, [RUN_RUNNING, RUN_COMPLETED]);
  assert.equal(store.isRunning("p1"), false);
});

test("get() returns the same snapshot reference until the state changes (required by useSyncExternalStore; a fresh object per read loops React)", async () => {
  const store = createEvaluationRunStore(async () => ({}));
  assert.equal(store.get("p1"), store.get("p1"), "idle");
  assert.equal(store.get("p1"), store.get("other"), "idle snapshots are shared");
  const run = store.run("p1");
  assert.equal(store.get("p1"), store.get("p1"), "running");
  await run;
  assert.equal(store.get("p1"), store.get("p1"), "completed");
});

test("a second request for a project that is already running is the same run, never a duplicate; other projects are independent", async () => {
  let calls = 0;
  const d = deferred();
  const store = createEvaluationRunStore(() => { calls += 1; return d.promise; });
  const a = store.run("p1");
  const b = store.run("p1");
  assert.equal(a, b);
  store.run("p2");
  assert.equal(calls, 2, "one request per project");
  d.resolve({});
  await Promise.all([a, b]);
  await store.run("p1");
  assert.equal(calls, 3, "after completion a new request starts a new run");
});

test("blockers and thrown errors are reported as failed with the real reason, and a later run recovers", async () => {
  const outcomes = [{ status: "BLOCKED_INCOMPLETE_INPUTS", blockers: ["budget is incomplete"] }, new Error("500 Internal Server Error"), { status: "EVALUATION_COMPLETE" }];
  const store = createEvaluationRunStore(async () => { const o = outcomes.shift(); if (o instanceof Error) throw o; return o; });
  await store.run("p1");
  assert.deepEqual([store.get("p1").status, store.get("p1").message], [RUN_FAILED, "budget is incomplete"]);
  await store.run("p1");
  assert.deepEqual([store.get("p1").status, store.get("p1").message], [RUN_FAILED, "500 Internal Server Error"]);
  await store.run("p1");
  assert.equal(store.get("p1").status, RUN_COMPLETED);
});

test("every producer-input save runs the evaluation through the shared single-flight store, and none calls beginEvaluation directly", () => {
  for (const file of [["components", "ContingencyElection.jsx"], ["components", "BudgetRail.jsx"], ["components", "IncentiveIntelligence.jsx"], ["components", "ContingencyDeployments.jsx"]]) {
    const src = read(...file);
    assert.match(src, /runEvaluation\(projectId\)/, file.join("/"));
    assert.doesNotMatch(src, /\bbeginEvaluation\b/, file.join("/"));
  }
  assert.match(read("lib", "evaluationRun.js"), /createEvaluationRunStore\(beginEvaluation\)/);
});

test("the Overview shows the real evaluation status and the controls are locked while it runs (no duplicate runs)", () => {
  const overview = read("screens", "production", "Overview.jsx");
  assert.match(overview, /<EvaluationStatus projectId=\{projectId\} onCompleted=\{refetch\} \/>/);
  const status = read("components", "EvaluationStatus.jsx");
  assert.match(status, /data-awaiting-update="true"/);
  assert.match(status, /data-eval-status="failed"/);
  assert.doesNotMatch(status.replace(/\/\/.*$/gm, ""), /%|<progress|percent/i, "no invented progress");
  assert.match(read("components", "ContingencyElection.jsx"), /disabled=\{saving \|\| run\.running\}/);
  assert.match(read("components", "BudgetRail.jsx"), /disabled=\{saving \|\| run\.running\}/);
});

test("saving on a project with retained (stale) results saves the input but starts no silent evaluation", () => {
  assert.match(read("components", "ContingencyElection.jsx"), /if \(evaluateOnSave\) await runEvaluation\(projectId\);\s*else setSavedNotEvaluated\(true\);/);
  assert.match(read("components", "ContingencyDeployments.jsx"), /if \(evaluateOnSave\) await runEvaluation\(projectId\);\s*else setSavedNotEvaluated\(true\);/);
  assert.match(read("components", "BudgetRail.jsx"), /evaluateOnSave=\{production\?\.evaluation_freshness !== "STALE"\}/);
  assert.match(read("screens", "production", "Overview.jsx"), /evaluateOnSave: production\?\.evaluation_freshness !== "STALE"/);
  assert.match(read("shell", "Inspector.jsx"), /evaluateOnSave=\{election\.evaluateOnSave !== false\}/);
});

test("Unknown stays distinct from stated: the Use control offers 'not stated' and the deployment control starts NOT_STATED with an explicit Clear, Cancel and a server-side category", () => {
  const line = read("components", "ContingencyElection.jsx");
  assert.match(line, /<option value="">— not stated<\/option>/);
  assert.match(line, /e\.target\.value === "" \? null : Number\(e\.target\.value\)/, "choosing not stated clears the fact (null), never 0");
  const dep = read("components", "ContingencyDeployments.jsx");
  assert.match(dep, /data-clear-deployments/);
  assert.match(dep, /data-cancel-deployments/);
  assert.match(dep, /submit\(Object\.keys\(payload\)\.length \? payload : null\)/, "an empty plan clears to not stated rather than posting zero");
  assert.doesNotMatch(dep, /destination_spend_category/, "the category is read from the budget by the server");
  assert.match(read("api.js"), /request\(`\/projects\/\$\{projectId\}\/contingency-deployments`/, "cineglobe base");
});
