import { useSyncExternalStore } from "react";
import { beginEvaluation } from "../api";
import { createEvaluationRunStore, RUN_RUNNING } from "./evaluationRunStore";

// The one evaluation-run store shared by every producer-input save (contingency, deployments, financing, jurisdiction preferences, Project Record).
export const evaluationRuns = createEvaluationRunStore(beginEvaluation);
export const runEvaluation = (projectId) => evaluationRuns.run(projectId);

// Snapshot objects are replaced on every change, so the reference is stable between changes.
export function useEvaluationRun(projectId) {
  const state = useSyncExternalStore(evaluationRuns.subscribe, () => evaluationRuns.get(projectId));
  return { ...state, running: state.status === RUN_RUNNING };
}
