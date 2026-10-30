// The producer-input evaluation is a server-side job with a hard deadline (POST /evaluation/begin starts or joins it and answers at once; GET /evaluation/status reports it).
// awaitEvaluation turns that into one awaited operation for the shared run store: it polls the real status, never invents progress, and reports the server's own failure,
// timeout or blocker text. `begin` / `status` are injected so the logic is testable without a network.
const TERMINAL_FAILURES = new Set(["timed_out", "failed", "blocked"]);
const MAX_STATUS_ERRORS = 3;
const LOST_CONTACT_GRACE_MS = 60_000;

export async function awaitEvaluation(begin, status, projectId, { intervalMs = 2000, sleep = (ms) => new Promise((r) => setTimeout(r, ms)), now = () => Date.now() } = {}) {
  const started = await begin(projectId);
  // Legacy / in-transaction shape (no job): the response is already the served result.
  if (!started || typeof started.deadline_at !== "number") return started;
  const giveUpAt = started.deadline_at * 1000 + LOST_CONTACT_GRACE_MS;
  let job = started;
  let errors = 0;
  while (job.status === "running") {
    await sleep(intervalMs);
    try {
      job = await status(projectId);
      errors = 0;
    } catch (err) {
      errors += 1;
      if (errors >= MAX_STATUS_ERRORS) throw new Error("Lost contact with the server while the evaluation was running. Your inputs are saved; reload and check, or retry.");
    }
    if (job.status === "idle") throw new Error("The server restarted while the evaluation was running and the run was lost. Your inputs are saved and the previous results are kept. Retry.");
    if (job.status === "running" && now() > giveUpAt) throw new Error("The evaluation did not report back by its deadline. Your inputs are saved and the previous results are kept. Retry.");
  }
  if (TERMINAL_FAILURES.has(job.status)) {
    return { status: job.result_status || job.status.toUpperCase(), jobStatus: job.status, message: job.message, blockers: job.status === "blocked" ? [job.message || "Evaluation is blocked on incomplete inputs."] : job.blockers };
  }
  return { status: job.result_status || "EVALUATION_COMPLETE", jobStatus: job.status, blockers: job.blockers || [] };
}
