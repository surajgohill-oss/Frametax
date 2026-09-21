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

// Every candidate admissible for `mode`, in the same canonical rank/NPC
// order productionOptions.js's rankOrNpcOrder already establishes for
// every other Workspace selection (never a second, independently-derived
// ordering). rankOrNpcOrder already restricts to is_fully_priced
// structures, so a rejected/authority-insufficient/unresolved candidate
// can never reach a ranked slot here — the one deliberate exception is
// Optimizer mode's own disclosed conditional grant/fund opportunities,
// appended strictly after every priced candidate.
export function admissibleForMode(allocated, mode) {
  if (!allocated?.structures) return [];
  const families = new Set(familiesForMode(mode));
  const priced = rankOrNpcOrder(allocated).filter((s) => families.has(s.classification));
  if (mode !== MODE_OPTIMIZER) return priced;
  const opportunities = allocated.structures.filter(
    (s) => s.classification === CONDITIONAL_OPPORTUNITY_CLASS,
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
