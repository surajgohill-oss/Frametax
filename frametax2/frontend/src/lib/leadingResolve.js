// Leading precedence for a served state: the producer's explicit "Set as Leading" choice (when it is still served), else the
// anchor / Current Location (structure null = baseline only).
export function resolveLeadingStructure(allocated, userLeadingId) {
  const structures = allocated?.structures || [];
  const byId = new Map(structures.map((s) => [s.structure_id, s]));
  // A saved choice may come from the optimizer candidate pool (e.g. a three-jurisdiction hybrid), not the ranked page.
  const chosen = userLeadingId
    ? byId.get(userLeadingId) || (allocated?.optimizer_candidates || []).find((s) => s.structure_id === userLeadingId)
    : null;
  if (chosen) return { structure: chosen, source: "user" };
  // PRODUCT RULE: a project sits at its anchor (Current Location) until the producer explicitly chooses "Set as Leading";
  // clearing the choice, or a choice that no longer exists, returns to the anchor. The canonical-selected and
  // leading-conditional structures are never substituted (a co-production never appears unprompted).
  return { structure: null, source: "baseline" };
}
