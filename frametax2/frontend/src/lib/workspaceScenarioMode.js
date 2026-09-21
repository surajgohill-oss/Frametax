// Workspace scenario-mode data wiring. Pure selection logic over the SAME
// allocated_structures data every other Workspace/Overview view already
// reads (see productionOptions.js's own header comment) — no new
// economics, no new ranking, nothing recalculated in React. Every family
// distinction below reads the backend's own `classification` field
// (app/services/structural_classification.py's canonical enum, stamped
// onto every served structure — GD-2 remediation) verbatim; never
// inferred from structure_type, treaty_slug, or a display label.

import { isBaselineStructure, rankOrNpcOrder } from "./productionOptions.js";

export const MODE_NORMAL = "normal";
export const MODE_OPTIMIZER = "optimizer";

// Normal mode: canonical single-jurisdiction/full-relocation results plus
// local jurisdiction stacks.
export const NORMAL_FAMILIES = ["SINGLE_JURISDICTION", "STACKED_PROGRAMS"];

// Optimizer mode: every canonical component/co-production/multilateral
// family the GD-2 remediation added a real classification for.
export const OPTIMIZER_FAMILIES = [
  "HYBRID_ANCHOR_COMPONENT",
  "OFFICIAL_COPRODUCTION",
  "COMBINED_COPRO_HYBRID_STACK",
  "MULTI_PRINCIPAL_MULTILATERAL",
];

// Conditional grant/fund opportunities (the backend's own
// CONDITIONAL_USER_FACT_REQUIRED classification — a real registry entry
// with a real project fact still missing, e.g. CO_PRO_OPPORTUNITY) are
// Optimizer-mode upside, disclosed but never a ranked/priced
// recommendation. Included in Optimizer's admissible pool ONLY after
// every real priced Optimizer candidate — never promoted ahead of one.
const CONDITIONAL_OPPORTUNITY_CLASS = "CONDITIONAL_USER_FACT_REQUIRED";

export function familiesForMode(mode) {
  return mode === MODE_OPTIMIZER ? OPTIMIZER_FAMILIES : NORMAL_FAMILIES;
}

// WORKSPACE_CANONICAL_JURISDICTION_WINNERS (2026-09-21) — ROOT CAUSE:
// Single Jurisdiction mode's admissible pool used to be reconstructed
// client-side from `allocated.structures` -- the bounded, OVERALL-rank-
// ordered served PAGE (candidates_page, limit 100), never the full
// retained set. Confirmed live against F#K Valentine's Day: that page is
// dominated by a different family (93 of the first 100 candidates by
// overall rank are HYBRID_ANCHOR_COMPONENT), so only 5 of the real 76
// jurisdiction winners the backend already computes ever reached the
// page at all -- the frontend was deduplicating/ranking a fundamentally
// incomplete, wrongly-ordered slice, which is what produced duplicate-
// looking and missing jurisdictions alike; it was never a backend
// discovery/pricing defect.
//
// The backend ALREADY serves the correct canonical projection:
// `allocated.best_per_jurisdiction` (canonical_production_view.py) -- one
// entry per jurisdiction, the real best (lowest verified NPC) EXECUTABLE
// candidate for that jurisdiction, computed from the full RETAINED set
// (never the bounded page), with its real economic_identity. Single
// Jurisdiction mode now consumes this projection DIRECTLY -- no frontend
// reconstruction from raw candidates, no dedup heuristic needed here (the
// backend's own retention already guarantees exactly one entry per
// jurisdiction).
function _singleJurisdictionCandidates(allocated) {
  const byJurisdiction = allocated?.best_per_jurisdiction || {};
  return Object.values(byJurisdiction)
    .filter(Boolean)
    .sort((a, b) => (a.npc_with_adjustments_usd ?? Infinity) - (b.npc_with_adjustments_usd ?? Infinity));
}

// Optimizer mode is different by design: a single jurisdiction is never
// enough (a hybrid/co-production/multilateral structure's whole point is
// multiple routed jurisdictions), so there is no per-jurisdiction winner
// concept to consume -- the canonical identity here is the FULL routed
// structure. Prefers the served `economic_identity` when present;
// otherwise falls back to the full routed combination (every participant
// jurisdiction plus every claimed program, both real, already-served
// fields) -- confirmed live: several of F#K Valentine's Day's real hybrid
// candidates share IDENTICAL participants and program_slugs, differing
// only by a few dollars of allocation-order rounding (the same canonical
// routed outcome discovered via different search paths, not materially
// distinct scenarios). `rankOrNpcOrder` has already sorted ascending by
// canonical NPC, so keeping the first candidate seen per key is exactly
// "the canonical best scenario for that identity" — never a second,
// independently-derived ranking.
function _optimizerScenarioKey(structure) {
  if (structure.economic_identity) return structure.economic_identity;
  const participants = [...(structure.participants || [])].sort().join(",");
  const programs = [...(structure.program_slugs || [])].sort().join(",");
  return `${participants}|${programs}`;
}

function _dedupeOptimizer(structures) {
  const seen = new Set();
  const out = [];
  for (const s of structures) {
    const key = _optimizerScenarioKey(s);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(s);
  }
  return out;
}

// GLOBE_SINGLE_AND_OPTIMIZER_WIRING (2026-09-21) — GD-4 backstop: the bounded,
// overall-rank-ordered `allocated.structures` page can omit a whole family
// entirely when a different family dominates it (confirmed by the Codex Globe
// data contract delta audit, GDC-002) -- a combined-co-production or
// multilateral candidate can be the real best-in-family and never once appear
// on the page. `allocated.top_by_structural_family` is the backend's own
// per-family winner block (canonical_production_view.py), pre-seeded with an
// honest [] for every priced family, computed from the FULL ranked candidate
// set -- never the bounded page. Normalizes its compact shape (`structural_
// family`) to the same `classification` key every page structure already
// carries, and marks it as fully priced (the block is documented as sourced
// from `_priced_entries` only) so it can flow through the exact same
// dedupe/tier logic as a page structure -- never a second, differently-shaped
// candidate type for downstream consumers (Globe, Workspace) to special-case.
function _familyBackstopCandidates(allocated) {
  const byFamily = allocated?.top_by_structural_family || {};
  const out = [];
  for (const [family, entries] of Object.entries(byFamily)) {
    for (const e of entries || []) {
      out.push({ ...e, classification: family, is_fully_priced: true, segments: e.segments || [], blockers: e.blockers || [] });
    }
  }
  return out;
}

// Every candidate admissible for `mode`. Single Jurisdiction mode reads
// the canonical best_per_jurisdiction projection directly (see above) --
// never a second, independently-derived ordering or dedup. Optimizer mode
// keeps its own canonical rank/NPC order (productionOptions.js's
// rankOrNpcOrder, the same order every other Workspace selection uses)
// with equivalent/duplicate full-structure identities collapsed to their
// single best representative; disclosed conditional grant/fund
// opportunities (CONDITIONAL_USER_FACT_REQUIRED — a real registry entry
// with a real project fact still missing) are appended strictly after
// every priced Optimizer candidate, never promoted ahead of one.
export function admissibleForMode(allocated, mode) {
  if (!allocated) return [];
  if (mode !== MODE_OPTIMIZER) return _singleJurisdictionCandidates(allocated);
  const families = new Set(OPTIMIZER_FAMILIES);
  const pagePriced = rankOrNpcOrder(allocated).filter((s) => families.has(s.classification));
  // GD-4 backstop (see _familyBackstopCandidates above): only ever ADDS a
  // family that has ZERO representation on the bounded page -- a family the
  // page DOES represent keeps its own real page-ranked candidates untouched,
  // never overridden or reordered by the backstop.
  const familiesOnPage = new Set(pagePriced.map((s) => s.classification));
  const backstop = _familyBackstopCandidates(allocated).filter(
    (s) => families.has(s.classification) && !familiesOnPage.has(s.classification),
  );
  const priced = _dedupeOptimizer([...pagePriced, ...backstop]);
  const opportunities = _dedupeOptimizer(
    (allocated.structures || []).filter((s) => s.classification === CONDITIONAL_OPPORTUNITY_CLASS),
  );
  return [...priced, ...opportunities];
}

// Six-slot Workspace composition for the active mode.
//   slot 1 — Current Location: the production's real baseline/anchor
//     structure. NEVER filtered by mode ("Current Location never changes
//     when modes switch").
//   slots 2-5 — the top four MODE-ADMISSIBLE scenarios (anchor excluded),
//     in canonical rank order.
//   slot 6 — `slot6Id` when it still resolves to a real mode-admissible
//     candidate beyond the first four; otherwise the canonical rank-5
//     admissible candidate. Never fabricated — fewer than six is a valid
//     result, exactly like the existing "Other Scenarios" contract.
// `dropdownOptions` is every mode-admissible candidate beyond the first
// four (a fixed pool, independent of the current slot-6 choice) — the
// same "select among already-generated candidates, never create one"
// contract the existing Other Scenarios control already uses; nothing is
// silently discarded, it is always reachable from the dropdown.
export function selectSixSlots(allocated, mode, slot6Id) {
  const anchor = allocated?.structures?.find(isBaselineStructure) || null;
  const pool = admissibleForMode(allocated, mode).filter(
    (s) => !anchor || s.structure_id !== anchor.structure_id,
  );
  const leading = pool.slice(0, 4);
  const dropdownOptions = pool.slice(4);
  const chosen = slot6Id ? dropdownOptions.find((s) => s.structure_id === slot6Id) : null;
  const slot6 = chosen || dropdownOptions[0] || null;
  const slots = [anchor, ...leading, slot6].filter(Boolean);
  return { anchor, leading, slot6, slots, dropdownOptions };
}
