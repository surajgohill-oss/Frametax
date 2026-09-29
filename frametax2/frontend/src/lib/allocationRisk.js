// F#K Valentine's Day economic/semantic regression fix (2026-09-03),
// item 3: the backend already computes and discloses administrative/
// discretionary allocation risk (award-authority discretion, competitive/
// capacity-limited allocation, or a mandatory preapproval step) for any
// structure whose program carries it — see canonical_evaluation.py's
// _competitive_allocation_disclosure(). It appends a prose disclosure to
// the served structure's `warnings` array, but until this fix no
// frontend file ever read that array, so a deterministically-priced but
// discretionary/preapproval-gated structure (e.g. Saudi Arabia's rebate)
// could present as an unconditional clean winner.
//
// This is a GENERIC detector keyed only on the stable backend-controlled
// disclosure prefix — never a jurisdiction/program name — so it works
// for any current or future program the backend discloses this way, not
// just Saudi. Pure logic, no JSX/React — same separation
// incentiveRate.js/productionOptions.js already use, so this stays
// independently unit-testable with plain `node` (format.jsx cannot be).
const ADMINISTRATIVE_ALLOCATION_RISK_PREFIX = "Administrative/allocation risk";

export function hasAdministrativeAllocationRisk(structure) {
  return !!(structure?.warnings || []).some((w) =>
    typeof w === "string" && w.startsWith(ADMINISTRATIVE_ALLOCATION_RISK_PREFIX)
  );
}

// Runtime wiring remediation (unresolved-calculation promotion): a SECOND,
// genuinely distinct unresolved-calculation disclosure — NOT the same as
// the structure's own `legal_review_required` boolean field
// (MultiProgramStackResult.legal_review_required, which reflects a hard
// statutory VIOLATION/mutual-exclusivity finding). This one fires when a
// real statutory stacking-deduction rule was found between two stacked
// programs but the reused spend_reduction calculator could not apply it
// (neither program is typed grant/regional_fund/discretionary_fund), so
// the combination's adjusted_incentive_usd is served as a real number
// that is NOT confirmed net of that deduction — a live production
// (Ontario's real OFTTC+OCASE stack) served exactly this state with
// `legal_review_required: false` alongside a confident "LEADING" badge.
// Keyed on the disclosure's own fixed, non-interpolated closing sentence
// (canonical_stack_bridge.py) — never a program/jurisdiction name.
const UNCONFIRMED_STACKING_DEDUCTION_TEXT =
  "adjusted_incentive_usd is therefore not confirmed net of this statutory deduction";

export function hasUnconfirmedStackingDeduction(structure) {
  return !!(structure?.warnings || []).some((w) =>
    typeof w === "string" && w.includes(UNCONFIRMED_STACKING_DEDUCTION_TEXT)
  );
}
