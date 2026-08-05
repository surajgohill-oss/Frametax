import { useCallback, useSyncExternalStore } from "react";

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
// No backend column exists for this yet (app/models/project.py carries no
// lifecycle field — confirmed by direct inspection). This store is a
// presentation-level mapping persisted to localStorage, keyed by
// production id, and is the one canonical mechanism every consumer reads
// (Sidebar, Settings, ProjectHeader/Hero, Today's lifecycle grouping) — no
// screen keeps a second copy of this state. The permanent home is a new
// column + PATCH route — documented for the data-model pass, out of scope
// for this migration.
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

  const meta = PROJECT_STATUSES.find((s) => s.key === status) || PROJECT_STATUSES[0];
  return { status: meta.key, meta, setStatus, statuses: PROJECT_STATUSES };
}
