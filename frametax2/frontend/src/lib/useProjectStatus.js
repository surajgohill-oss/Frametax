import { useCallback, useSyncExternalStore } from "react";

// Canonical production lifecycle — a producer-set stage for where the
// production stands, distinct from anything the optimizer computes.
//
// Evaluation comes FIRST: CineGlobe's initial job is determining whether
// the project can be produced effectively — candidate jurisdictions,
// qualifying structures, treaty possibilities, comparative economics —
// before the production proceeds into development and packaging.
// Financing is deliberately NOT a lifecycle stage.
//
// No backend column exists for this yet (app/models/project.py carries no
// lifecycle field — confirmed by direct inspection). This store is a
// presentation-level mapping persisted to localStorage, keyed by
// production id. The permanent home is a new column + PATCH route —
// documented for the data-model pass, out of scope for this migration.
export const PROJECT_STATUSES = [
  { key: "evaluation", label: "Evaluation", tier: "blue",
    description: "Jurisdiction analysis, qualifying structures, treaty possibilities, and comparative production economics — determining whether and where the project can be produced effectively." },
  { key: "development", label: "Development", tier: "silver",
    description: "Script and budget forming; the production has proceeded beyond initial evaluation." },
  { key: "packaging", label: "Packaging", tier: "gold",
    description: "Cast, finance, and structure being assembled around the evaluated plan." },
  { key: "pre_production", label: "Pre-Production", tier: "gold",
    description: "Structure locked; crewing, locations, and schedules being executed." },
  { key: "production", label: "Production", tier: "gold",
    description: "Principal photography underway." },
  { key: "post_production", label: "Post-Production", tier: "jade",
    description: "Editorial, VFX, music, and mix." },
  { key: "delivery", label: "Delivery", tier: "jade",
    description: "Deliverables, certification, and audit toward release." },
  { key: "released", label: "Released", tier: "jade",
    description: "In release; incentive claims settling." },
  { key: "archived", label: "Archived", tier: "charcoal",
    description: "Closed. Record and Reports are the primary surfaces." },
];

// Values persisted by the previous 3-status scheme map forward without
// corrupting anything a user already set.
const LEGACY_MAP = {
  in_development: "development",
  in_evaluation: "evaluation",
  in_production: "production",
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
