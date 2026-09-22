// Workspace scenario-mode data wiring. Pure selection logic over the SAME
// allocated_structures data every other Workspace/Overview view already
// reads (see productionOptions.js's own header comment) — no new
// economics, no new ranking, nothing recalculated in React. Every family
// distinction below reads the backend's own `classification` field
// (app/services/structural_classification.py's canonical enum, stamped
// onto every served structure — GD-2 remediation) verbatim; never
// inferred from structure_type, treaty_slug, or a display label.

import { isBaselineStructure } from "./productionOptions.js";

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

// COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21): no longer used to
// dedupe the priced optimizer pool itself (`allocated.optimizer_candidates`
// is already deduplicated by real economic_identity server-side, and every
// priced entry always carries one — see canonical_production_view.py).
// Retained only for the much smaller CONDITIONAL_USER_FACT_REQUIRED
// "opportunities" list below, where a real economic_identity is not always
// present; the participants+programs fallback stays scoped to that list.
// COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21) — ROOT CAUSE (supersedes
// the GD-4 backstop this function used to apply): the bounded, overall-rank-
// ordered `allocated.structures` page AND `allocated.top_by_structural_family`
// (capped at TYPE_TOP=100 per family) are BOTH lossy views over the backend's
// full retained/priced set -- confirmed live for F#K Valentine's Day: 411 real
// PRICED HYBRID_ANCHOR_COMPONENT candidates exist, of which the page carried
// only 93 and the family backstop only 100. The old "add a family's backstop
// entries only when the page has ZERO representation for that family" logic
// never helped here, because HYBRID_ANCHOR_COMPONENT WAS represented on the
// page (just incompletely) — so 318 real, priced, producer-selectable
// optimizer candidates were silently unreachable in every UI surface.
//
// `allocated.optimizer_candidates` (canonical_production_view.py) was the
// backend's complete fix for that: every PRICED candidate in an optimizer
// family, uncapped, deduplicated by real economic_identity. It is still
// served (and still complete) for auditability, but it dedupes only by
// exact economic_identity — multiple search/enumeration iterations of the
// SAME producer-facing route (identical participants/programs/routing,
// differing only by which internal budget-category label triggered a leg,
// and a few dollars of rounding) each keep their own row. Confirmed live:
// F#K Valentine's Day's optimizer_candidates[0..2] are all "Manitoba
// (principal) + Newfoundland & Labrador + Italy" at materially the same
// economics — Workspace and Globe repeated the same apparent card three
// times in a row.
//
// PRODUCER_OPTIMIZER_SCENARIO_CANONICALIZATION (2026-09-21):
// `allocated.optimizer_scenarios` is the backend's canonical producer-
// facing projection — one entry per materially distinct route (grouped by
// classification/primary jurisdiction/participants/routed jurisdiction-to-
// program topology/treaty identity, never by structure_id, economic_
// identity or search order), each the group's own lowest-verified-NPC
// representative, uncapped, already sorted by canonical NPC ascending.
// Every optimizer-consuming UI surface reads THIS, never the raw
// optimizer_candidates collection.
function _optimizerScenarios(allocated) {
  return allocated?.producer_optimizer_options || [];
}

// Every candidate admissible for `mode`. Single Jurisdiction mode reads
// the canonical best_per_jurisdiction projection directly (see above);
// Optimizer mode reads the canonical material producer projection directly.
// Conditional/unpriced opportunities and exhaustive 3+ jurisdiction search
// rows stay available in the backend audit collections but never enter the
// ordinary producer UI.
export function admissibleForMode(allocated, mode) {
  if (!allocated) return [];
  if (mode !== MODE_OPTIMIZER) return _singleJurisdictionCandidates(allocated);
  return _optimizerScenarios(allocated);
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
