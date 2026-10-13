// Per-project evaluation-run state for producer-input saves, derived only from the real operation: `running` while the actual evaluation request is in flight, `completed` when it
// returns, `failed` when it throws or reports blockers. There is no queue and no progress percentage (none exists); a second request for a project that is already running is the same run,
// never a duplicate. The prior figures on screen are "awaiting update" exactly while `running`.
export const RUN_IDLE = "idle";
export const RUN_RUNNING = "running";
export const RUN_COMPLETED = "completed";
export const RUN_FAILED = "failed";

// One frozen idle snapshot: useSyncExternalStore requires get() to return the SAME reference until the state changes.
const IDLE = Object.freeze({ status: RUN_IDLE, message: null, finishedAt: null });

export function createEvaluationRunStore(begin) {
  const runs = new Map();             // projectId -> { status, message, finishedAt }
  const inflight = new Map();         // projectId -> Promise
  const listeners = new Set();
  const emit = () => listeners.forEach((l) => l());
  const set = (projectId, value) => { runs.set(projectId, value); emit(); };

  function get(projectId) {
    return runs.get(projectId) || IDLE;
  }

  function run(projectId) {
    if (!projectId) return Promise.resolve(get(projectId));
    if (inflight.has(projectId)) return inflight.get(projectId);
    set(projectId, { status: RUN_RUNNING, message: null, finishedAt: null });
    const promise = (async () => {
      try {
        const result = await begin(projectId);
        const blocked = result && Array.isArray(result.blockers) && result.blockers.length > 0;
        set(projectId, blocked
          ? { status: RUN_FAILED, message: result.blockers[0] || "Evaluation is blocked on incomplete inputs.", finishedAt: Date.now() }
          : { status: RUN_COMPLETED, message: null, finishedAt: Date.now() });
      } catch (err) {
        set(projectId, { status: RUN_FAILED, message: (err && err.message) || "The evaluation failed.", finishedAt: Date.now() });
      } finally {
        inflight.delete(projectId);
      }
      return get(projectId);
    })();
    inflight.set(projectId, promise);
    return promise;
  }

  function subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  return { get, run, subscribe, isRunning: (projectId) => inflight.has(projectId) };
}
