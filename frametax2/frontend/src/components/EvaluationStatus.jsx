import { runEvaluation, useEvaluationRun } from "../lib/evaluationRun";

// Genuine evaluation state for the project's producer-input saves: shown while the real evaluation runs (the figures on screen are from the previous inputs), after it fails (with
// the actual reason and a retry), and once it completes. No queue and no progress percentage: neither exists.
export default function EvaluationStatus({ projectId, onCompleted, compact = false }) {
  const run = useEvaluationRun(projectId);
  if (!projectId || run.status === "idle") return null;
  if (run.running) {
    return (
      <div className={`eval-status${compact ? " eval-status-compact" : ""}`} role="status" aria-live="polite" data-eval-status="running" data-awaiting-update="true">
        Recalculating… the figures shown are from the previous inputs and update when the evaluation completes.
      </div>
    );
  }
  if (run.status === "failed") {
    return (
      <div className={`eval-status eval-status-error${compact ? " eval-status-compact" : ""}`} role="alert" data-eval-status="failed">
        The evaluation did not complete: {run.message}{" "}
        <button type="button" className="ghost-action" onClick={() => runEvaluation(projectId).then(() => onCompleted?.())}>Retry</button>
      </div>
    );
  }
  return (
    <div className={`eval-status${compact ? " eval-status-compact" : ""}`} role="status" aria-live="polite" data-eval-status="completed">
      Recalculated with the saved inputs.
    </div>
  );
}

// Shown after a producer input is saved on a project whose results are retained from an earlier engine: the input is saved, but no evaluation is started silently (a recalculation can take
// a long time and is only ever started on an explicit request).
export function RetainedSaveNote() {
  return (
    <div className="eval-status eval-status-compact" role="status" data-eval-status="saved-awaiting-recalculate">
      Saved. The results shown are retained from an earlier engine; use Recalculate on the Project Record to apply this input.
    </div>
  );
}
