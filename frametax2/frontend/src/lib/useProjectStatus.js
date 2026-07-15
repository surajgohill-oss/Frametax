import { useCallback, useSyncExternalStore } from "react";

// Company workflow status — a producer-set label for where a deal stands,
// distinct from anything the optimizer computes. No backend field exists
// for this yet (app/models/project.py and app/schemas/project.py carry no
// status column — confirmed by direct inspection of the CineGlobe backend
// this session); this is deliberately NOT the same concept as the DB
// model's StructureStatus (DRAFT/CALCULATING/COMPLETE/ERROR/ARCHIVED),
// which is per-candidate calculation-engine state, not company workflow.
//
// Persisted to localStorage, keyed by production id, so the choice
// survives a reload without inventing a backend write path. This is a
// known, documented limitation (see CLAUDE.md SESSION DELTA) — the
// correct permanent home is a new column + PATCH /projects/{id} route,
// out of scope for a frontend-only implementation pass.
export const PROJECT_STATUSES = [
  { key: "in_development", label: "In Development", tier: "silver",
    description: "Script/budget still forming. The optimizer may run informally; nothing is being filed." },
  { key: "in_evaluation", label: "In Evaluation", tier: "blue",
    description: "Structure comparison underway. The production has not yet been accepted by the company." },
  { key: "in_production", label: "In Production", tier: "gold",
    description: "Structure locked, shooting or posting. Record and Reports become the primary surfaces." },
];

const STORAGE_PREFIX = "cineglobe:project-status:";
const DEFAULT_STATUS = "in_evaluation"; // "has not yet been accepted by the company" — the honest default

function readStatus(productionId) {
  if (!productionId) return DEFAULT_STATUS;
  try {
    return localStorage.getItem(STORAGE_PREFIX + productionId) || DEFAULT_STATUS;
  } catch {
    return DEFAULT_STATUS;
  }
}

// Multiple screens each call useProjectStatus(productionId) independently
// (SecondaryNav, Today, Settings — same pattern as useCineGlobe, no shared
// context). localStorage's own "storage" event never fires in the tab that
// made the write, so without a subscription a status change in Settings
// would leave every other already-mounted instance (e.g. the header chip)
// stale until a full reload. useSyncExternalStore is the correct React
// primitive for exactly this — external mutable store synced into React,
// notifying every subscribed instance for the same productionId.
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

export function useProjectStatus(productionId) {
  const status = useSyncExternalStore(
    (listener) => subscribe(productionId, listener),
    () => readStatus(productionId),
  );

  const setStatus = useCallback((key) => {
    try {
      if (productionId) localStorage.setItem(STORAGE_PREFIX + productionId, key);
    } catch {
      // localStorage unavailable (private mode, etc.) — status still
      // updates for this session, just doesn't persist across reload.
    }
    notify(productionId);
  }, [productionId]);

  const meta = PROJECT_STATUSES.find((s) => s.key === status) || PROJECT_STATUSES[1];
  return { status, meta, setStatus, statuses: PROJECT_STATUSES };
}
