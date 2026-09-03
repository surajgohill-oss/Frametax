// Pure computation for Today's Hero and FX strip — no React, no DOM, so
// this module is independently testable (see
// scripts/test_today_compute.mjs, run with plain `node`; this frontend
// has no test runner installed, and none is being introduced here). This
// is also why buildLeaderFxItems below does NOT import flagEmoji from
// ../lib/format.jsx (a .jsx file plain `node` can't load) — it returns
// each item's `jurisdiction` and the caller (components/FXStrip.jsx, a
// real React module) resolves the flag at render time. Same single
// flagEmoji implementation, just called from the presentation layer
// instead of duplicated here.

// The base currency every economics payload prices in. A leader
// structure whose own jurisdiction already uses this currency needs no
// conversion at all — CineGlobe Overview FX Strip + Vertical Scrolling
// closeout: this used to fall through to buildLeaderFxItems' generic
// "no snapshot on file" branch and render a dishonest "rate unavailable"
// for a USD-jurisdiction leader (e.g. any US-state structure), when the
// truthful state is "no conversion applies" — see noConversion below.
const BASE_CURRENCY = "USD";

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

// The dynamic fourth (Nth) FX slot: one cell per DISTINCT local currency
// among a structure's real participants — one cell for a single-
// jurisdiction structure, two for a genuine multi-jurisdiction one,
// deduplicated so two participants sharing a currency (e.g. two Eurozone
// jurisdictions) never render twice. Every rate is read verbatim from
// economics.fx_horizons (the SAME dataset feeding the fixed trio in
// buildFxItems — no second fetch, no frontend FX math).
//
// Extracted from Workspace.jsx (CineGlobe Overview FX Strip + Vertical
// Scrolling closeout) so Workspace and Overview share the exact same FX
// engine rather than each carrying its own copy — REUSE, never a second
// implementation. `structure` is deliberately NOT always the producer's
// manually-selected Leading Structure — see each caller's own fallback
// (bestPricedCandidate when neither a Leading selection nor a canonical
// rank-1 exists). When `structure` is null, this returns an empty array —
// a fake, unresolved "—" block must never render just to fill the slot.
export function buildLeaderFxItems(economics, structure, label) {
  if (!structure) return [];
  const horizons = economics?.fx_horizons || {};
  const jurisdictionCurrency = economics?.jurisdiction_currency || {};
  const participants = structure?.participants?.length
    ? structure.participants
    : (structure?.primary_jurisdiction ? [structure.primary_jurisdiction] : []);

  const seenCodes = new Set();
  const items = [];
  for (const jurisdiction of participants) {
    const iso2 = jurisdiction.split("-")[0].toUpperCase();
    // Generic chain, no jurisdiction/currency special-cased here:
    // jurisdiction -> ISO2 -> economics.jurisdiction_currency (the SAME
    // canonical registry map served for the fixed trio) -> currency code.
    // No mapping on file: show the jurisdiction's own code rather than
    // silently dropping the cell.
    const code = jurisdictionCurrency[iso2] || iso2;
    if (seenCodes.has(code)) continue; // dedupe — never a repeated currency cell
    seenCodes.add(code);
    // Truthful no-conversion state: the structure's own currency IS the
    // base currency the economics payload already prices in — there is
    // no real FX pair to show, and no snapshot entry will ever exist for
    // USD/USD. Manufacturing one (or falling through to "rate
    // unavailable", which reads as a data gap rather than a fact) would
    // be exactly the fabricated-pair failure mode item 5 warns against.
    if (code === BASE_CURRENCY) {
      items.push({ code, jurisdiction, isLeader: true, leaderLabel: label, available: true, noConversion: true });
      continue;
    }
    const h = horizons[code];
    if (!h || h.current == null) {
      items.push({ code, jurisdiction, available: false, isLeader: true, leaderLabel: label });
      continue;
    }
    const deltaPct = h["12m"] != null ? ((h["12m"] - h.current) / h.current) * 100 : null;
    // Same 5-decimal display precision buildFxItems() uses for the fixed
    // three, so leader cells never read visually inconsistent with their
    // siblings — reverse is still always 1/current, computed here, never a
    // second stored constant.
    items.push({
      code, jurisdiction, isLeader: true, leaderLabel: label, available: true,
      current: Number(h.current.toFixed(FX_DISPLAY_DECIMALS)), reverse: Number((1 / h.current).toFixed(FX_DISPLAY_DECIMALS)), deltaPct,
    });
  }
  return items;
}
