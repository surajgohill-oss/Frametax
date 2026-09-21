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

// WORKSPACE_VISUAL_REGRESSION_CORRECTION (2026-09-22): the served
// structure payload does not (yet) populate a canonical `economic_
// identity` for multi_program/ordinary_component_hybrid candidates —
// confirmed live against F#K Valentine's Day (every candidate in both
// families serves economic_identity: null). Never invented client-side
// from scratch; the SAME real, already-served fields the identity would
// have been built from are used instead:
//   Normal mode (single_jurisdiction / local stacks) — the canonical
//     identity is the jurisdiction itself: a producer's headline view
//     needs ONE best scenario per distinct jurisdiction, not every
//     stacking permutation of the same jurisdiction (confirmed live:
//     F#K Valentine's Day's real data has FOUR distinct Ontario
//     candidates -- on_ofttc+ocase, ca_federal_cptc+on_ofttc,
//     on_opstc+ocase, ca_federal_cptc+ca_qc_pstc -- each a genuinely
//     different program combination with different NPC, but all reading
//     as "Ontario" on the headline card, crowding four of six slots with
//     one jurisdiction). Keyed on primary_jurisdiction alone -- the same
//     concept canonical_production_view.py's own best_per_jurisdiction
//     block already applies server-side for the frozen Jurisdictions
//     Globe, just consumed here from the per-structure field it already
//     serves rather than a second server round-trip.
//   Optimizer mode (component/co-production/multilateral hybrids) — a
//     single jurisdiction is never enough (a hybrid's whole point is
//     multiple routed jurisdictions), so the canonical identity is the
//     full routed combination: every participant jurisdiction plus every
//     claimed program, both already real, served fields. Confirmed live:
//     three of F#K Valentine's Day's real hybrid candidates share the
//     IDENTICAL participants (CA-MB, CA-NL, IT) and IDENTICAL program_
//     slugs, differing only by a few dollars of allocation-order rounding
//     -- the same canonical routed outcome discovered via different
//     search paths, not three distinct scenarios.
// Either way: `rankOrNpcOrder` has ALREADY sorted candidates by canonical
// NPC ascending before this runs, so keeping the FIRST candidate seen per
// key is exactly "the canonical best scenario for that identity" — never
// a second, independently-derived ranking.
function _canonicalScenarioKey(structure, mode) {
  if (structure.economic_identity) return structure.economic_identity;
  if (mode === MODE_OPTIMIZER) {
    const participants = [...(structure.participants || [])].sort().join(",");
    const programs = [...(structure.program_slugs || [])].sort().join(",");
    return `${participants}|${programs}`;
  }
  return structure.primary_jurisdiction || structure.structure_id;
}

function _dedupeByCanonicalIdentity(structures, mode) {
  const seen = new Set();
  const out = [];
  for (const s of structures) {
    const key = _canonicalScenarioKey(s, mode);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(s);
  }
  return out;
}

// Every candidate admissible for `mode`, in the same canonical rank/NPC
// order productionOptions.js's rankOrNpcOrder already establishes for
// every other Workspace selection (never a second, independently-derived
// ordering), with equivalent/duplicate canonical scenarios collapsed to
// their single best (lowest-NPC) representative. rankOrNpcOrder already
// restricts to is_fully_priced structures, so a rejected/authority-
// insufficient/unresolved candidate can never reach a ranked slot here —
// the one deliberate exception is Optimizer mode's own disclosed
// conditional grant/fund opportunities, appended strictly after every
// priced candidate (also deduplicated, by the same Optimizer-mode key).
export function admissibleForMode(allocated, mode) {
  if (!allocated?.structures) return [];
  const families = new Set(familiesForMode(mode));
  const priced = _dedupeByCanonicalIdentity(
    rankOrNpcOrder(allocated).filter((s) => families.has(s.classification)),
    mode,
  );
  if (mode !== MODE_OPTIMIZER) return priced;
  const opportunities = _dedupeByCanonicalIdentity(
    allocated.structures.filter((s) => s.classification === CONDITIONAL_OPPORTUNITY_CLASS),
    mode,
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
