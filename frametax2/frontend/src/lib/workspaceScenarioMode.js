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
// retained set. The backend ALREADY serves the correct canonical
// projection: `allocated.best_per_jurisdiction` — one entry per
// jurisdiction, the real best (lowest verified NPC) EXECUTABLE candidate
// for that jurisdiction, computed from the full RETAINED set. Single
// Jurisdiction mode consumes this projection DIRECTLY — no frontend
// reconstruction from raw candidates, no dedup heuristic needed here (the
// backend's own retention already guarantees exactly one entry per
// jurisdiction).
function _singleJurisdictionCandidates(allocated) {
  const byJurisdiction = allocated?.best_per_jurisdiction || {};
  // SINGLE_JURISDICTION_GLOBE_WIRING (2026-09-23): explicit economic_identity
  // tie-break — two different jurisdictions' winners landing on the exact
  // same NPC is real but rare; without a deterministic second key, JS sort
  // stability would fall back to Object.values() insertion order (the
  // backend dict's own key order), which is a real ordering but not one this
  // module defends or documents. economic_identity is unique per structure,
  // so this guarantees a fully deterministic order across re-renders and
  // re-fetches, never re-deriving or recomputing NPC itself.
  return Object.values(byJurisdiction)
    .filter(Boolean)
    .sort((a, b) => {
      const npcDiff = (a.npc_with_adjustments_usd ?? Infinity) - (b.npc_with_adjustments_usd ?? Infinity);
      if (npcDiff !== 0) return npcDiff;
      return String(a.economic_identity ?? "").localeCompare(String(b.economic_identity ?? ""));
    });
}

// GLOBE_WORKSPACE_CANONICAL_WIRING_COMPLETE (2026-09-22) — ROOT CAUSE (supersedes the
// PRODUCER_OPTIMIZER_PRESENTATION_CORRECTION pass this replaces): that pass pointed
// every Optimizer surface at `allocated.producer_optimizer_options`, a collection the
// backend built by DROPPING every candidate below a $100K savings threshold and every
// 3+-jurisdiction candidate outright. CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md
// found this made producer_optimizer_options_total exactly 0 for all four real
// productions in the acceptance database — the Optimizer surface was empty everywhere,
// while dozens of real, priced, executable structures (Little Utopia alone: 66 saving
// more than $200,000) were invisible. The controlling product contract is explicit:
// "Recommendation thresholds affect priority, not visibility."
//
// canonical_production_view.py now serves three first-class collections built from the
// SAME complete, never-filtered `optimizer_scenarios` array (one entry per materially
// distinct route, already deduplicated by real economic_identity, uncapped):
//   - `recommended_optimizer_options` — savings > $100K (2-jurisdiction) or > $200K
//     (3+-jurisdiction); a PRIORITY split, not a narrower universe.
//   - `evaluated_optimizer_alternatives` — every other executable entry (below-threshold,
//     neutral, or costs-more than Current Location) — real, visible, never hidden.
//   - `optimizer_opportunities_requiring_facts` — real, disclosed co-production/
//     multilateral opportunities (a registered treaty/framework exists) that cannot be
//     priced without a real ownership-split/cultural-test fact not yet on file. Never
//     executable, never eligible to become the leading/selected structure.
// `producer_optimizer_options` remains served as a backward-compatible ALIAS for
// `recommended_optimizer_options` only — this module never reads it as the sole pool.

const _TIER_RANK = { PRACTICAL_HYBRID: 0, FORMAL_COPRODUCTION: 1, ADVANCED_MULTI_JURISDICTION: 2 };
const _EVAL_STATUS_RANK = { EVALUATED_ALTERNATIVE: 0, NEUTRAL: 1, COSTS_MORE: 2, BASELINE_UNRESOLVED: 3 };

function _npcOf(s) {
  return s.npc_verified_usd ?? s.npc_with_adjustments_usd ?? Infinity;
}

// Recommended ordering (controlling product contract): simplest qualifying structure
// first (tier: Practical -> Formal -> Advanced), then savings descending, then NPC
// ascending, then economic_identity as the final deterministic tie-break.
function _sortRecommended(list) {
  return [...list].sort((a, b) => {
    const tierDiff = (_TIER_RANK[a.practicality_tier] ?? 9) - (_TIER_RANK[b.practicality_tier] ?? 9);
    if (tierDiff !== 0) return tierDiff;
    const savingsDiff = (b.savings_vs_current_usd ?? -Infinity) - (a.savings_vs_current_usd ?? -Infinity);
    if (savingsDiff !== 0) return savingsDiff;
    const npcDiff = _npcOf(a) - _npcOf(b);
    if (npcDiff !== 0) return npcDiff;
    return (a.economic_identity || "").localeCompare(b.economic_identity || "");
  });
}

// Evaluated-alternative ordering (controlling product contract): positive savings below
// threshold, then neutral, then costs-more, then NPC ascending with a stable identity
// tie-break.
function _sortEvaluatedAlternatives(list) {
  return [...list].sort((a, b) => {
    const rankDiff = (_EVAL_STATUS_RANK[a.recommendation_status] ?? 9) - (_EVAL_STATUS_RANK[b.recommendation_status] ?? 9);
    if (rankDiff !== 0) return rankDiff;
    const npcDiff = _npcOf(a) - _npcOf(b);
    if (npcDiff !== 0) return npcDiff;
    return (a.economic_identity || "").localeCompare(b.economic_identity || "");
  });
}

// THE one shared Optimizer projection. Every Optimizer-consuming surface (Overview,
// Workspace cards/dropdown, Lanes, Map, Split, Full Project Globe, hover, Inspector)
// must call this — never independently filter allocated_structures by savings,
// jurisdiction count, family, or page position.
export function optimizerProjection(allocated) {
  const recommended = _sortRecommended(allocated?.recommended_optimizer_options || allocated?.producer_optimizer_options || []);
  const evaluated = _sortEvaluatedAlternatives(allocated?.evaluated_optimizer_alternatives || []);
  const opportunities = allocated?.optimizer_opportunities_requiring_facts || [];
  return {
    recommended,
    evaluated,
    opportunities,
    executableTotal: allocated?.optimizer_executable_total ?? allocated?.optimizer_scenarios_total ?? (recommended.length + evaluated.length),
    recommendedTotal: allocated?.recommended_optimizer_options_total ?? recommended.length,
    evaluatedTotal: allocated?.evaluated_optimizer_alternatives_total ?? evaluated.length,
    opportunitiesTotal: allocated?.optimizer_opportunities_requiring_facts_total ?? opportunities.length,
  };
}

// Every candidate admissible for `mode`, in producer-priority rank order. Single
// Jurisdiction mode reads the canonical best_per_jurisdiction projection directly (see
// above). Optimizer mode reads the complete recommended + evaluated-alternative pool —
// Needs-More-Facts opportunities are NEVER part of this ranked/selectable pool (see
// selectSixSlots below for how they are surfaced separately instead).
export function admissibleForMode(allocated, mode) {
  if (!allocated) return [];
  if (mode !== MODE_OPTIMIZER) return _singleJurisdictionCandidates(allocated);
  const { recommended, evaluated } = optimizerProjection(allocated);
  return [...recommended, ...evaluated];
}

// Six-slot Workspace composition for the active mode.
//   slot 1 — Current Location: the production's real baseline/anchor
//     structure. NEVER filtered by mode ("Current Location never changes
//     when modes switch").
//   slots 2-5 — Optimizer mode: the first four RECOMMENDED outcomes, never
//     padded with evaluated alternatives when fewer than four recommended
//     outcomes exist (an honest, shorter rack is correct). Jurisdictions
//     mode: unchanged — the top four best_per_jurisdiction candidates.
//   slot 6 — the fifth recommended outcome (Optimizer) / fifth candidate
//     (Jurisdictions), or `slot6Id` when it still resolves to a real
//     admissible candidate beyond the first four. Never fabricated —
//     fewer than six is a valid result.
// `dropdownOptions` — remaining RECOMMENDED (Optimizer) / remaining
// candidates (Jurisdictions) beyond the first five, the existing "Other
// Scenarios" contract, unchanged shape.
// `dropdownEvaluatedAlternatives` — Optimizer mode only: every evaluated
// alternative, in a separately labeled section, selectable for slot 6 but
// never silently promoted into slots 2-5.
// `dropdownOpportunities` — Optimizer mode only: every Needs-More-Facts
// opportunity, in a separately labeled, NON-executable section — never
// selectable as slot 6 / leading structure.
export function selectSixSlots(allocated, mode, slot6Id) {
  const anchor = allocated?.structures?.find(isBaselineStructure) || null;

  if (mode !== MODE_OPTIMIZER) {
    const pool = _singleJurisdictionCandidates(allocated).filter(
      (s) => !anchor || s.structure_id !== anchor.structure_id,
    );
    const leading = pool.slice(0, 4);
    const remaining = pool.slice(4);
    const chosen = slot6Id ? remaining.find((s) => s.structure_id === slot6Id) : null;
    const slot6 = chosen || remaining[0] || null;
    // SINGLE_JURISDICTION_GLOBE_WIRING (2026-09-23): the dropdown's own
    // default option ("— <current slot 6 label> —", rendered by the caller)
    // already represents whichever winner occupies slot 6. Without this
    // exclusion, that same jurisdiction winner ALSO appeared a second time
    // inside the optgroup list — a real duplicate entry (e.g. two literal
    // "Ontario" rows), present on every production with more than 5
    // canonical winners, not just an explicit-override edge case. Mirrors
    // the Optimizer branch below, which already excludes its own slot6 id.
    const excludeId = slot6 ? slot6.structure_id : null;
    const dropdownOptions = remaining.filter((s) => s.structure_id !== excludeId);
    const slots = [anchor, ...leading, slot6].filter(Boolean);
    return {
      anchor, leading, slot6, slots, dropdownOptions,
      dropdownEvaluatedAlternatives: [], dropdownOpportunities: [],
    };
  }

  const { recommended, evaluated, opportunities } = optimizerProjection(allocated);
  const recPool = recommended.filter((s) => !anchor || s.structure_id !== anchor.structure_id);
  const evalPool = evaluated.filter((s) => !anchor || s.structure_id !== anchor.structure_id);
  // OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25) — ROOT CAUSE (confirmed
  // live against F#K Valentine's Day: exactly 4 real recommended options):
  // slots 2-6 (five cards) used to fill ONLY from `recPool.slice(0,4)` for
  // the leading four, with slot 6 defaulting to `remainingRecommended[0] ||
  // null` — NEVER falling back to an evaluated alternative when recPool had
  // fewer than 5 entries. FVD's 4 recommended options filled the leading
  // four exactly, leaving `remainingRecommended` empty and slot 6 null —
  // Workspace showed only 4 Optimizer cards (Current Location + 4), not the
  // controlling contract's required Current Location + 5. The controlling
  // contract is explicit: "Slots 2-6: first five executable Optimizer
  // options, recommended first... if fewer than five recommendations exist,
  // fill remaining slots with the best Evaluated Alternatives." `combined`
  // below is exactly that — recPool (already recommended-first via
  // _sortRecommended) followed by evalPool (already ordered via
  // _sortEvaluatedAlternatives) — so slicing the first five ALWAYS prefers
  // every real recommended option before ever reaching an evaluated one,
  // and naturally generalizes to any recommended count (not just the FVD=4
  // case): 66/107/112 recommended (LU/BH/LLS) still fill all five leading
  // slots from recPool alone, unchanged from before.
  const combined = [...recPool, ...evalPool];
  const leading = combined.slice(0, 4);
  const remaining = combined.slice(4);
  // An explicit producer choice (slot6Id) may select ANY remaining
  // executable option, recommended or evaluated — that is a deliberate
  // producer action, never an automatic promotion. Opportunities are never
  // slot-6-eligible (see dropdownOpportunities below — visible, disabled).
  const chosen = slot6Id ? remaining.find((s) => s.structure_id === slot6Id) : null;
  const slot6 = chosen || remaining[0] || null;
  // Dropdown sections must remain genuinely distinct — track which of
  // `leading`/`slot6` came from recPool vs evalPool so "Remaining
  // Recommended" never lists an evaluated alternative and vice versa; never
  // make an evaluated alternative appear recommended anywhere in this
  // contract, including the dropdown's own section membership.
  const usedIds = new Set([...leading, slot6].filter(Boolean).map((s) => s.structure_id));
  const dropdownOptions = recPool.filter((s) => !usedIds.has(s.structure_id));
  const dropdownEvaluatedAlternatives = evalPool.filter((s) => !usedIds.has(s.structure_id));
  const slots = [anchor, ...leading, slot6].filter(Boolean);
  return {
    anchor, leading, slot6, slots,
    dropdownOptions, dropdownEvaluatedAlternatives,
    dropdownOpportunities: opportunities,
  };
}
