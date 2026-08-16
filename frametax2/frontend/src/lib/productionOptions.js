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
//    that only relocation_cost_normalized candidates rank numerically).
// 2. Sixth slot: the best not-yet-shown structure whose treaty_slug is
//    explicitly set, if one exists; otherwise the next valid/comparable
//    option in the same existing order.
// Never manufactures a sixth option -- fewer than six is a valid result.
export function selectTopOptions(allocated) {
  if (!allocated?.ranking || !allocated?.structures) return [];
  const structById = new Map(allocated.structures.map((s) => [s.structure_id, s]));
  const pricedRanked = allocated.ranking.filter((r) => r.is_fully_priced);

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
