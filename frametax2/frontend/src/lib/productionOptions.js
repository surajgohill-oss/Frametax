// Overview UI contract — "Production Options" (up to six primary
// structure cards on Overview, replacing the previous 4-slot per-
// jurisdiction representative grid). Pure selection/classification logic
// over the SAME allocated_structures/ranking data every other screen
// already reads (Workspace's ScenarioCard, Scenarios.jsx) — no new
// economics, no new ranking, nothing recalculated. Kept in a plain .js
// module (not the .jsx component) so it can be unit-tested directly, the
// same separation globeFit.js/globeData.js already use.

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

function _hasUpsideGap(structure) {
  const claiming = (structure.segments || []).filter((sg) => sg.claims_incentive);
  const floors = claiming.map((sg) => sg.rate_floor).filter((r) => r != null);
  const ceilings = claiming.map((sg) => sg.rate_ceiling ?? sg.rate_floor).filter((r) => r != null);
  if (!floors.length || !ceilings.length) return false;
  const floor = Math.min(...floors);
  const ceiling = Math.max(...ceilings);
  return Math.round(floor * 10000) !== Math.round(ceiling * 10000);
}

export function selectMaxPotentialCard(allocated, excludeIds) {
  if (!allocated?.structures) return null;
  const candidates = allocated.structures.filter((s) => !excludeIds.has(s.structure_id));

  let bestFund = null;
  let bestFundCap = 0;
  for (const s of candidates) {
    const cap = (s.conditional_programs || []).reduce((sum, p) => sum + (p.documented_cap_usd || 0), 0);
    if (cap > bestFundCap) { bestFundCap = cap; bestFund = s; }
  }
  if (bestFund) return { structure: bestFund, isOpportunity: true, potentialUsd: bestFundCap };

  const treatyOpportunity = candidates.find(
    (s) => s.treaty_slug || s.structure_type === "treaty_coproduction" || s.candidate_status === "STATUS_CO_PRO_OPPORTUNITY",
  );
  if (treatyOpportunity) return { structure: treatyOpportunity, isOpportunity: true, potentialUsd: null };

  const withOwnUpside = candidates
    .filter((s) => s.is_fully_priced && _hasUpsideGap(s))
    .sort((a, b) => (b.npc_with_adjustments_usd ?? 0) - (a.npc_with_adjustments_usd ?? 0));
  if (withOwnUpside.length) return { structure: withOwnUpside[0], isOpportunity: false, potentialUsd: null };

  return null;
}

export function selectTopFour(allocated) {
  if (!allocated?.ranking || !allocated?.structures) return [];
  const ordered = _rankOrNpcOrder(allocated);
  const firstThree = ordered.slice(0, 3);
  const shownIds = new Set(firstThree.map((s) => s.structure_id));

  const maxPotential = selectMaxPotentialCard(allocated, shownIds);
  if (maxPotential) {
    return [...firstThree, { ...maxPotential.structure, __isOpportunity: maxPotential.isOpportunity, __potentialUsd: maxPotential.potentialUsd }];
  }
  const fourth = ordered.find((s) => !shownIds.has(s.structure_id));
  if (fourth) return [...firstThree, fourth];
  return firstThree;
}

// Card status — item 10's four exact single-line states. `leadingId`:
// the producer's manual Leading selection (activeStructure's own
// identity), same generic concept every other Leading/Top-Priced
// distinction in this app already uses (FXStrip, Budget Rail) — never a
// second "leading" derivation.
export function cardStatus(structure, cardIndex, leadingId) {
  if (structure.__isOpportunity) return "OPPORTUNITY";
  if (leadingId ? structure.structure_id === leadingId : cardIndex === 0) return "LEADING";
  if (_hasUpsideGap(structure)) return "OPTIMIZE";
  return "VIABLE";
}
