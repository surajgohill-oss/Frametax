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
// {stageMeta: {key}, budget, npc, momentum: {rank}}. Returns exactly 3
// entries, in HERO_STAGE_KEYS order, each a real sum/count over the
// productions array — npc sums only productions with a real (non-null)
// priced NPC, never substituting budget or zero for an unpriced one;
// attention counts productions whose momentum rank is Blocked(0) or
// Stalled(1), the same two-tier definition Today's hero attention badge
// already uses.
export function buildHeroStages(statuses, productions) {
  return HERO_STAGE_KEYS.map((key) => {
    const meta = statuses.find((s) => s.key === key) || { key, label: key };
    const inStage = productions.filter((p) => p.stageMeta.key === key);
    return {
      key,
      label: meta.label,
      count: inStage.length,
      budget: inStage.reduce((sum, p) => sum + (p.budget || 0), 0),
      npc: inStage.reduce((sum, p) => sum + (p.npc || 0), 0),
      attention: inStage.filter((p) => (p.momentum?.rank ?? 99) <= 1).length,
      productions: inStage,
    };
  });
}

// FX strip currencies, in order. GBP and EUR have real sourced snapshot
// data on the backend (FX_RATE_SNAPSHOTS — see production_normalization.py);
// CAD has none anywhere in this codebase (no jurisdiction maps to CAD, no
// snapshot entry exists) — rendered as an honest unavailable state, never
// a fabricated rate.
export const FX_STRIP_CODES = ["EUR", "CAD", "GBP"];

// Foreign-currency flag per group — Unicode regional-indicator emoji, no
// new asset dependency. The flag identifies the FOREIGN currency (EU /
// Canada / UK), never a USD flag on every pair. EUR uses the EU flag.
export const FX_FLAGS = { EUR: "🇪🇺", CAD: "🇨🇦", GBP: "🇬🇧" };

// Producer-facing precision for both quotation directions.
const FX_DISPLAY_DECIMALS = 5;

// fxHorizons: the real economics.fx_horizons payload, keyed by currency
// code, each {current, "1m", "6m", "12m"} (nulls where no sourced
// snapshot exists). Returns exactly FX_STRIP_CODES.length entries.
//
// Each available item carries BOTH quotation directions:
//   current = local-currency units per 1 USD (the canonical stored rate,
//             read verbatim from the backend snapshot — the only real
//             number in play).
//   reverse = 1 / current, computed here, every render — never a second
//             stored constant, so the two directions can never drift
//             out of mathematical agreement with each other.
// The 12-month delta is computed against the canonical (USD/{code})
// direction only; it is never reapplied with the same sign to the
// reverse pair, since a currency strengthening against USD in the
// USD/{code} quote is the SAME move as {code}/USD weakening — the
// percentage magnitude carries, the interpretation does not, so no
// second delta is fabricated for the reverse direction here at all.
export function buildFxItems(fxHorizons) {
  return FX_STRIP_CODES.map((code) => {
    const h = fxHorizons?.[code];
    const flag = FX_FLAGS[code];
    if (!h || h.current == null) {
      return { code, flag, available: false };
    }
    const deltaPct = h["12m"] != null ? ((h["12m"] - h.current) / h.current) * 100 : null;
    return {
      code,
      flag,
      available: true,
      current: Number(h.current.toFixed(FX_DISPLAY_DECIMALS)),
      reverse: Number((1 / h.current).toFixed(FX_DISPLAY_DECIMALS)),
      horizon12m: h["12m"],
      deltaPct,
    };
  });
}
