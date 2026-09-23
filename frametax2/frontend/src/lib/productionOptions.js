// Overview UI contract — "Production Options" (up to six primary
// structure cards on Overview, replacing the previous 4-slot per-
// jurisdiction representative grid). Pure selection/classification logic
// over the SAME allocated_structures/ranking data every other screen
// already reads (Workspace's ScenarioCard, Scenarios.jsx) — no new
// economics, no new ranking, nothing recalculated. Kept in a plain .js
// module (not the .jsx component) so it can be unit-tested directly, the
// same separation globeFit.js/globeData.js already use.
//
// Does NOT import workspaceScenarioMode.js's optimizerProjection() —
// workspaceScenarioMode.js itself imports isBaselineStructure from THIS
// module, so importing back would be a circular dependency. Reads the
// same `recommended_optimizer_options` (falling back to the
// `producer_optimizer_options` backward-compatible alias) field directly
// instead — the identical data optimizerProjection() reads, just without
// its re-sort (selectMaxPotentialCard only needs the first entry, and the
// backend already serves recommended_optimizer_options pre-sorted
// Practical -> Formal -> Advanced, NPC ascending).

export const CLASSIFICATIONS = {
  current: { key: "current", label: "Current / Base Production", accent: "gold" },
  relocation: { key: "relocation", label: "Full Relocation", accent: "jade" },
  hybrid: { key: "hybrid", label: "Hybrid / Component", accent: "amber" },
  treaty: { key: "treaty", label: "Official Treaty Co-Production", accent: "silver" },
};

// `structure_type === "single_country"` is set by the backend ONLY for
// the production's own home jurisdiction (canonical_evaluation.py:
// "single_country" if code == inputs.jurisdiction_code else
// "full_relocation" -- true for both the generic path and
// little_utopia_state.py, which uses the literal string exactly once,
// for its base Mauritius structure). `is_baseline` is the same fact on
// the generic canonical_production_view.py entries, but little_utopia_
// state.py's own richer per-structure dict does not carry that field at
// all -- checking structure_type first means Current/Base classifies
// correctly on BOTH data sources, not just the generic one.
export function isBaselineStructure(entry) {
  return !!(entry.is_baseline || entry.structure_type === "single_country");
}

// Canonical served wiring repair (Codex Defect 2) — is_directly_comparable
// on a RANKING entry only exists on the generic canonical_production_view.py
// path (added this batch). little_utopia_state.py's own rank_allocated_
// structures() has no such field and never will need one: LU's rich
// per-structure pricing already includes real travel/FX/in-kind deltas
// (unlike the generic path's hard-set zeros), so every one of ITS ranked
// candidates already IS directly comparable by construction -- which is
// exactly what its existing is_fully_priced always meant. Falling back to
// is_fully_priced when is_directly_comparable is absent therefore
// preserves LU's existing, already-correct behavior unchanged, while the
// generic path (which always sets the field explicitly) gets the real fix.
export function isDirectlyComparable(rankingEntry) {
  return rankingEntry?.is_directly_comparable ?? rankingEntry?.is_fully_priced ?? false;
}

// The UI must stop treating every multi-jurisdiction structure as a
// "co-production." `treaty_slug` is the one EXPLICIT field the backend
// already sets only when a real bilateral/multilateral treaty applies
// (app/calculators/treaty_engine.py's _BILATERAL/_MULTILATERAL tables,
// threaded through structure_generator.py / production_structure_composer.py) --
// classification reads that flag, never infers treaty status from a
// structure having two participants or from its structure_type string.
export function classifyStructure(entry) {
  if (isBaselineStructure(entry)) return CLASSIFICATIONS.current;
  if (entry.treaty_slug) return CLASSIFICATIONS.treaty;
  if (entry.structure_type === "full_relocation") return CLASSIFICATIONS.relocation;
  return CLASSIFICATIONS.hybrid;
}

// Top Six selection (UI only, see CineGlobe Overview UI contract):
// 1. First five valid/comparable options from the EXISTING ranking order
//    (allocated.ranking, already sorted by npc_with_adjustments_usd --
//    canonical_production_view.py / little_utopia_state.py's own rule
//    that only is_directly_comparable candidates rank numerically).
// 2. Sixth slot: the best not-yet-shown structure whose treaty_slug is
//    explicitly set, if one exists; otherwise the next valid/comparable
//    option in the same existing order.
// Never manufactures a sixth option -- fewer than six is a valid result.
//
// Canonical served wiring repair (Codex Defect 2): filters on
// is_directly_comparable, NOT is_fully_priced. Priced-but-not-regionally-
// comparable structures (FVD has 29) are real, differentiated economics —
// they belong in Scenarios' Review section (see selectReviewOptions
// below), never silently promoted into "the six primary options" just
// because they happen to be priced.
export function selectTopOptions(allocated) {
  if (!allocated?.ranking || !allocated?.structures) return [];
  const structById = new Map(allocated.structures.map((s) => [s.structure_id, s]));
  const pricedRanked = allocated.ranking.filter(isDirectlyComparable);

  const firstFive = pricedRanked.slice(0, 5)
    .map((r) => structById.get(r.structure_id))
    .filter(Boolean);
  const shownIds = new Set(firstFive.map((s) => s.structure_id));

  const treatyCandidates = allocated.structures.filter(
    (s) => s.is_fully_priced && s.treaty_slug && !shownIds.has(s.structure_id),
  );
  let sixth = null;
  if (treatyCandidates.length > 0) {
    sixth = treatyCandidates.reduce((best, s) => {
      const bestNpc = best?.npc_with_adjustments_usd ?? Infinity;
      const sNpc = s.npc_with_adjustments_usd ?? Infinity;
      return sNpc < bestNpc ? s : best;
    }, null);
  } else if (pricedRanked.length > 5) {
    sixth = structById.get(pricedRanked[5].structure_id) || null;
  }

  const options = [...firstFive];
  if (sixth && !shownIds.has(sixth.structure_id)) options.push(sixth);
  return options.slice(0, 6);
}

export function qpeOf(structure) {
  return structure.segments?.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0) || 0;
}

// CineGlobe Overview Top Four (final adversarial repair pass, 2026-09-03).
// Card 1-3: the three highest-ranked CURRENTLY MODELED structures, same
// existing ranking order/filter selectTopOptions already uses
// (is_directly_comparable). Card 4: the highest-value LEGITIMATE
// potentially-optimized opportunity not already shown — never fabricated,
// always sourced from real, disclosed canonical optimizer fields:
//   1. A structure carrying real conditional_programs (grants/funds with
//      their own documented_cap_usd — a genuine published ceiling, e.g.
//      Canada Media Fund/Telefilm) — ranked by total disclosed cap.
//   2. A real, disclosed treaty/co-production opportunity
//      (treaty_slug set, or the CO_PRO_OPPORTUNITY terminal status).
//   3. A currently-modeled structure with its OWN genuine rate_floor <
//      rate_ceiling gap (a real, already-resolved-by-the-optimizer
//      upside on that structure itself) not already in cards 1-3.
//   4. Fallback per item 9: the canonical next-best current modeled
//      structure (4th-ranked), same semantics as cards 1-3 — never a
//      fabricated "opportunity" when no legitimate one exists.
// `isOpportunity: true` (cases 1-2) means this card represents a real,
// disclosed pathway that is NOT current earned economics — the caller
// must render it with OPPORTUNITY status and must never format its
// figure through compactIncentiveRate (that would misrepresent a
// disclosed cap/opportunity as an earned resolved rate).
// The "top ranked, currently modeled" ordering item 9's Cards 1-3 need is
// a BROADER concept than isDirectlyComparable (which narrowly means
// "regionally/currency comparable to the production's own home
// jurisdiction" — Little Utopia's own real data has exactly ONE such
// structure, its Mauritius baseline, which made Card 1-3 collapse to a
// single entry when this reused isDirectlyComparable, caught live in the
// rendered app: header read "Top Structures 2", not 4). The correct,
// already-established convention is Workspace.jsx's own
// visibleStructures() ordering — rank first (allocated.ranking's own
// order), tie-broken by ascending NPC for a priced structure with no
// formal rank — reused here instead of a second, narrower selection
// rule, over every is_fully_priced structure.
// Exported (not just internal) so Workspace.jsx's own lane ordering can
// reuse this exact function instead of carrying a second, independently-
// maintained copy of the same rank-then-NPC rule (item 7: "Do not
// duplicate business logic independently in two React components").
export function rankOrNpcOrder(allocated) {
  return _rankOrNpcOrder(allocated);
}

function _rankOrNpcOrder(allocated) {
  const rankById = new Map((allocated.ranking || []).map((r) => [r.structure_id, r]));
  return [...allocated.structures]
    .filter((s) => s.is_fully_priced)
    .sort((a, b) => {
      const ra = rankById.get(a.structure_id)?.rank ?? Infinity;
      const rb = rankById.get(b.structure_id)?.rank ?? Infinity;
      if (ra !== rb) return ra - rb;
      const an = a.npc_with_adjustments_usd ?? Infinity;
      const bn = b.npc_with_adjustments_usd ?? Infinity;
      return an - bn;
    });
}

// F#K Valentine's Day economic/semantic regression fix (2026-09-03):
// this used to sum every conditional_programs[].documented_cap_usd and
// present the total as "Potential up to $X" — for FVD's real Manitoba
// candidate that summed FIVE unrelated NATIONAL funds' own per-project
// CEILINGS (Canada Media Fund $10M + Telefilm CFFF $5M + Telefilm Export
// $550K + Manitoba Film & Music $550K = $16.1M) for a production with a
// $4.5M total source budget — a program-wide cap sized for "major drama"
// productions much larger than this one, presented as if it were this
// project's own achievable potential. A per-project cap is real and
// disclosable, but summing several unrelated funds' own maximums (each
// independently competitive/discretionary, never simultaneously
// guaranteed) is not a project-level figure at all (item 5.C/5.D: a
// program cap/maximum must never be presented as the project's
// calculated incentive, and must never exceed what's mathematically
// permissible for this project). Fix: disclose the REAL fund names/count
// (still real, disclosed, non-fabricated data) without manufacturing a
// dollar figure no single fund, let alone their sum, actually guarantees
// this specific production.
export function selectMaxPotentialCard(allocated, excludeIds) {
  if (!allocated?.structures) return null;
  const recommended = allocated.recommended_optimizer_options || allocated.producer_optimizer_options || [];
  const practical = recommended.find((s) => !excludeIds.has(s.structure_id));
  if (practical) {
    return { structure: practical, isOpportunity: false, isProducerOptimizer: true, potentialUsd: null, fundCount: 0, fundNames: [] };
  }
  return null;
}

// CineGlobe Overview 2x2 anchor/scenario composition (history-based
// restoration, 2026-09-03). The approved 2x2 grid genuinely existed
// (commit ec283e5, "Incentive Intelligence 2x2 grid") — its own real
// category was "Recommended" (gold, the rank-1 structure), not a
// dedicated anchor/current-production concept; the ONE canonical field
// this codebase already uses for "current/base production structure" is
// isBaselineStructure()/is_baseline (backend-sourced -- see its own
// header comment above), reused here rather than inventing a second
// concept. Card 1 is always the production's real baseline/current
// structure when one exists in the allocated set; Cards 2-3 are the two
// highest-ranked alternatives EXCLUDING the anchor (never array
// position); Card 4 is the strongest legitimate optimization opportunity
// not already shown (selectMaxPotentialCard, unchanged from the prior
// pass — its own real-data sourcing already satisfies item 5's
// requirement list), falling back to the next-best ranked alternative
// when no legitimate opportunity exists (never fabricated).
export function selectAnchorLeadingOptimized(allocated) {
  if (!allocated?.structures) return [];
  const anchor = allocated.structures.find(isBaselineStructure) || null;
  const ordered = Object.values(allocated.best_per_jurisdiction || {})
    .filter(Boolean)
    .sort((a, b) => (a.npc_with_adjustments_usd ?? Infinity) - (b.npc_with_adjustments_usd ?? Infinity))
    .filter(
    (s) => !anchor || s.structure_id !== anchor.structure_id,
  );
  const leading = ordered.slice(0, 2);
  const cards = anchor ? [anchor, ...leading] : leading.length ? ordered.slice(0, 3) : [];
  const shownIds = new Set(cards.map((s) => s.structure_id));

  const maxPotential = selectMaxPotentialCard(allocated, shownIds);
  if (maxPotential) {
    cards.push({
      ...maxPotential.structure,
      __isOpportunity: maxPotential.isOpportunity,
      __isProducerOptimizer: maxPotential.isProducerOptimizer,
      __potentialUsd: maxPotential.potentialUsd,
      __fundCount: maxPotential.fundCount,
      __fundNames: maxPotential.fundNames,
    });
  }
  return cards.slice(0, 4);
}

// Card status — the restored ANCHOR/LEADING/LEADING/OPTIMIZED vocabulary
// (item 10 of the prior pass's LEADING/OPTIMIZE/VIABLE/OPPORTUNITY
// wording is superseded by this history-based restoration). `cardIndex`
// is the position selectAnchorLeadingOptimized itself returned the
// structure at — never re-derived from array order elsewhere, so Anchor
// can never be assigned to array position 0 by accident when
// selectAnchorLeadingOptimized had no real baseline to put there (the
// `isBaselineStructure` check below is the actual authority, cardIndex
// is only a hint consistent with it by construction).
export function cardStatus(structure, cardIndex) {
  if (structure.__isOpportunity) return "OPTIMIZED";
  if (cardIndex === 0 && isBaselineStructure(structure)) return "ANCHOR";
  if (structure.__isProducerOptimizer) return "OPTIMIZED";
  return "LEADING";
}
