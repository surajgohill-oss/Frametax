// ALTERNATIVE_TERMINOLOGY (2026-10-01): the ONE producer-facing vocabulary for
// an optimizer structure's canonical status. "Recommended" over-directs a
// producer; the same canonical backend fields are presented as alternatives:
//   first canonical RECOMMENDED            -> LEADING ALTERNATIVE
//   further canonical RECOMMENDED          -> STRONG ALTERNATIVE
//   executable, positive saving, not RECOMMENDED -> COST-SAVING REFERENCE
//   executable, neutral / more expensive / unresolved -> REFERENCE ALTERNATIVE
//   missing-fact opportunity               -> NEEDS MORE FACTS
//   genuine rejection / unpriceable        -> UNAVAILABLE (+ its specific reason)
// Pure presentation over served fields (recommendation_status,
// savings_vs_current_usd, candidate_status): nothing is recomputed, no field or
// status is renamed, and the $100,000-per-added-jurisdiction policy is untouched.
// "Better than the anchor" alone never yields Leading/Strong.
export const ALT = {
  LEADING: "LEADING ALTERNATIVE",
  STRONG: "STRONG ALTERNATIVE",
  COST_SAVING: "COST-SAVING REFERENCE",
  REFERENCE: "REFERENCE ALTERNATIVE",
  NEEDS_FACTS: "NEEDS MORE FACTS",
  UNAVAILABLE: "UNAVAILABLE",
};

const UNAVAILABLE_STATUSES = new Set([
  "RULE_REJECTED", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", "FEASIBILITY_REVIEW_REQUIRED",
  "QUALIFICATION_HARD_FAIL", "RULE_DATA_INCOMPLETE",
]);

// `leadingId`: structure_id of the first canonical RECOMMENDED option
// (optimizerProjection(...).recommended[0]); null when none qualifies.
export function alternativeLabel(structure, leadingId = null) {
  if (!structure) return ALT.REFERENCE;
  const status = structure.candidate_status;
  if (status === "CO_PRO_OPPORTUNITY") return ALT.NEEDS_FACTS;
  if (UNAVAILABLE_STATUSES.has(status)) return ALT.UNAVAILABLE;
  if (structure.recommendation_status === "RECOMMENDED" || structure.is_recommended === true) {
    return leadingId && structure.structure_id === leadingId ? ALT.LEADING : ALT.STRONG;
  }
  const savings = structure.savings_vs_current_usd;
  if (structure.recommendation_status !== "COSTS_MORE" && structure.recommendation_status !== "NEUTRAL"
      && typeof savings === "number" && savings > 0) return ALT.COST_SAVING;
  return ALT.REFERENCE;
}

// Title-case form for running text ("Leading Alternative").
export function alternativeTitle(label) {
  return String(label).toLowerCase().replace(/(^|[\s-])([a-z])/g, (m, a, b) => a + b.toUpperCase());
}
