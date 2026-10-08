// Leading precedence for a served state: the producer's saved choice (when it is still in the served page), else the
// canonical selected structure (rank 1), else the canonical leading-conditional structure, else none (baseline only).
export function resolveLeadingStructure(allocated, userLeadingId) {
  const structures = allocated?.structures || [];
  const byId = new Map(structures.map((s) => [s.structure_id, s]));
  // A saved choice may come from the optimizer candidate pool (e.g. a three-jurisdiction hybrid), not the ranked page.
  const chosen = userLeadingId
    ? byId.get(userLeadingId) || (allocated?.optimizer_candidates || []).find((s) => s.structure_id === userLeadingId)
    : null;
  if (chosen) return { structure: chosen, source: "user" };
  const canonical = allocated?.canonical_selected_structure_id;
  if (canonical && byId.has(canonical)) return { structure: byId.get(canonical), source: "canonical" };
  const conditional = allocated?.leading_conditional_structure?.structure_id;
  if (conditional && byId.has(conditional)) return { structure: byId.get(conditional), source: "canonical_conditional" };
  return { structure: null, source: "baseline" };
}
