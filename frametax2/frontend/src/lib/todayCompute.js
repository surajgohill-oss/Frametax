// Pure computation for Today's Hero and FX strip — no React, no DOM, so
// this module is independently testable (see
// scripts/test_today_compute.mjs, run with plain `node`; this frontend
// has no test runner installed, and none is being introduced here).

// The Today hero shows exactly these three canonical CineGlobe lifecycle
// stages, in this exact order. Evaluation precedes Development, per the
// fixed canonical order (Evaluation -> Development -> Packaging ->
// Pre-Production -> Production -> Post -> Delivery -> Released ->
// Archived, from useProjectStatus's own PROJECT_STATUSES). No rollup, no
// alternative labels, no fourth category.
export const HERO_STAGE_KEYS = ["evaluation", "development", "production"];

// statuses: PROJECT_STATUSES (key/label pairs). productions: array of
// {stageMeta: {key}, budget}. Returns exactly 3 entries, in
// HERO_STAGE_KEYS order, each a real sum over the productions array.
export function buildHeroStages(statuses, productions) {
  return HERO_STAGE_KEYS.map((key) => {
    const meta = statuses.find((s) => s.key === key) || { key, label: key };
    const inStage = productions.filter((p) => p.stageMeta.key === key);
    return {
      key,
      label: meta.label,
      count: inStage.length,
      budget: inStage.reduce((sum, p) => sum + (p.budget || 0), 0),
    };
  });
}

// FX strip currencies, in order. GBP and EUR have real sourced snapshot
// data on the backend (FX_RATE_SNAPSHOTS — see production_normalization.py);
// CAD has none anywhere in this codebase (no jurisdiction maps to CAD, no
// snapshot entry exists) — rendered as an honest unavailable state, never
// a fabricated rate.
export const FX_STRIP_CODES = ["EUR", "CAD", "GBP"];

// fxHorizons: the real economics.fx_horizons payload, keyed by currency
// code, each {current, "1m", "6m", "12m"} (nulls where no sourced
// snapshot exists). Returns exactly FX_STRIP_CODES.length entries.
export function buildFxItems(fxHorizons) {
  return FX_STRIP_CODES.map((code) => {
    const h = fxHorizons?.[code];
    if (!h || h.current == null) {
      return { code, available: false };
    }
    const deltaPct = h["12m"] != null ? ((h["12m"] - h.current) / h.current) * 100 : null;
    return {
      code,
      available: true,
      current: h.current,
      horizon12m: h["12m"],
      deltaPct,
    };
  });
}
