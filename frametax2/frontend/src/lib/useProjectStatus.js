import { useCallback, useEffect, useRef, useSyncExternalStore } from "react";
import { patchProject } from "../api";

// Canonical production lifecycle — a producer-set stage for where the
// production stands, distinct from anything the optimizer computes.
// PERMANENT PROJECT RULE (see CAPABILITY_LEDGER.md, "Production Lifecycle
// Rule"): every production has exactly one explicit, user-controlled
// stage, in this fixed order — Evaluation -> Development -> Production ->
// Completed -> Archived. It is persisted project metadata, never inferred
// from optimizer status or production facts. Archived is non-destructive
// (see the rule for the full statement).
//
// Evaluation comes FIRST: CineGlobe's initial job is determining whether
// the project can be produced effectively — candidate jurisdictions,
// qualifying structures, treaty possibilities, comparative economics —
// before the production proceeds into development. Financing is
// deliberately NOT a lifecycle stage.
//
// Project Library Phase C: Project.lifecycle (app/models/project.py) is now
// the persistent source of truth, written via PATCH /api/v1/projects/{id}.
// localStorage remains the synchronous read + offline/bounded fallback that
// every consumer already relies on (Sidebar, Settings, ProjectHeader/Hero,
// Today's lifecycle grouping) — no screen keeps a second copy of this state.
// Callers that have the backend's project_id/lifecycle (from
// production.project_id / production.lifecycle) pass them as the optional
// second argument so this hook can reconcile localStorage to the backend
// value on first read and write changes through to the backend; callers
// that don't (or before the backend value has loaded) still work exactly
// as before, localStorage-only.
export const PROJECT_STATUSES = [
  { key: "evaluation", label: "Evaluation", tier: "blue",
    description: "Jurisdiction analysis, qualifying structures, treaty possibilities, and comparative production economics — determining whether and where the project can be produced effectively." },
  { key: "development", label: "Development", tier: "silver",
    description: "Script, budget, cast, finance, and structure forming; the production has proceeded beyond initial evaluation, through packaging and pre-production." },
  { key: "production", label: "Production", tier: "gold",
    description: "Principal photography underway." },
  { key: "completed", label: "Completed", tier: "jade",
    description: "Photography wrapped; post, delivery, and release are settling. Still an active production, not yet closed." },
  { key: "archived", label: "Archived", tier: "charcoal",
    description: "Closed — non-destructive. The record, files, and historical analysis remain intact and retrievable from Project Library; it no longer counts as an active production." },
];

// Values persisted by earlier, more granular lifecycle schemes map forward
// without corrupting anything a user already set — never a data loss on
// this rename, just a fold into the nearest canonical bucket.
const LEGACY_MAP = {
  in_development: "development",
  in_evaluation: "evaluation",
  in_production: "production",
  packaging: "development",
  pre_production: "development",
  post_production: "completed",
  delivery: "completed",
  released: "completed",
};

const STORAGE_PREFIX = "cineglobe:project-status:";
const DEFAULT_STATUS = "evaluation"; // new productions default to Evaluation

function readStatus(productionId) {
  if (!productionId) return DEFAULT_STATUS;
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + productionId) || DEFAULT_STATUS;
    return LEGACY_MAP[raw] || raw;
  } catch {
    return DEFAULT_STATUS;
  }
}

// Multiple mounted instances (sidebar production row, project header
// selector, Settings, Today) must stay synchronized — localStorage's own
// "storage" event never fires in the writing tab, so useSyncExternalStore
// with an in-module subscriber map is the correct primitive.
const subscribers = new Map(); // productionId -> Set<() => void>

function subscribe(productionId, listener) {
  if (!productionId) return () => {};
  if (!subscribers.has(productionId)) subscribers.set(productionId, new Set());
  subscribers.get(productionId).add(listener);
  return () => subscribers.get(productionId)?.delete(listener);
}

function notify(productionId) {
  subscribers.get(productionId)?.forEach((listener) => listener());
}

export function useProjectStatus(productionId, backend = {}) {
  const { projectId, backendLifecycle } = backend;

  const status = useSyncExternalStore(
    (listener) => subscribe(productionId, listener),
    () => readStatus(productionId),
  );

  // One-time-per-mount reconciliation: once the backend's persisted
  // lifecycle arrives, adopt it into the localStorage cache this hook
  // already reads synchronously. Guarded so it never fires more than once
  // per productionId per component instance — it must not fight a user's
  // in-session change or re-run on every unrelated re-render.
  const reconciledFor = useRef(null);
  useEffect(() => {
    if (!productionId || !backendLifecycle) return;
    if (reconciledFor.current === productionId) return;
    reconciledFor.current = productionId;
    const backendKey = LEGACY_MAP[backendLifecycle.toLowerCase()] || backendLifecycle.toLowerCase();
    if (backendKey !== status) {
      try {
        localStorage.setItem(STORAGE_PREFIX + productionId, backendKey);
      } catch {
        // ignore — falls through to session-only state via notify()
      }
      notify(productionId);
    }
  }, [productionId, backendLifecycle, status]);

  const setStatus = useCallback((key) => {
    try {
      if (productionId) localStorage.setItem(STORAGE_PREFIX + productionId, key);
    } catch {
      // localStorage unavailable (private mode, etc.) — status still
      // updates for this session, just doesn't persist across reload.
    }
    notify(productionId);

    // Phase C write-through. Fire-and-forget from the UI's perspective —
    // localStorage above is what the dropdown already reads synchronously,
    // so a slow or failed PATCH never blocks or reverts the visible
    // selection; it only means the backend falls behind until retried.
    if (projectId) {
      patchProject(projectId, { lifecycle: key.toUpperCase() }).catch((err) => {
        console.error("[useProjectStatus] failed to persist lifecycle to backend:", err);
      });
    }
  }, [productionId, projectId]);

  const meta = PROJECT_STATUSES.find((s) => s.key === status) || PROJECT_STATUSES[0];
  return { status: meta.key, meta, setStatus, statuses: PROJECT_STATUSES };
}
