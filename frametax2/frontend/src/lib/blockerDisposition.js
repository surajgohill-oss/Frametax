// GLOBE_WIRING_REMEDIATION (2026-10-01): one pure classifier turning an
// already-served canonical rejection/blocked row (candidate_status +
// rejection_reason_class + the engine's own reason sentence) into the
// producer-facing disposition the Globe hover and Inspector must state --
// instead of one unexplained "blocked" red. Never invents a disposition:
// every branch is keyed off a real canonical status/class (or, for the one
// ambiguous status, a phrase the engine itself wrote), and the engine's own
// reason sentence is always carried through verbatim for the detail line.

export const BLOCKER_KIND = {
  AWARD_RATE: "award_rate_confirmation_required",
  AUTHORITY: "authority_insufficient",
  ELIGIBILITY: "eligibility_conditions_unmet",
  SELECTIVE: "selective_non_guaranteed",
  SUPERSEDED: "superseded",
  PROHIBITED: "prohibited_combination",
  MIN_SPEND: "minimum_spend_not_met",
  QUALIFICATION: "qualification_hard_fail",
  DOMINATED: "economically_dominated",
  OTHER: "rule_rejected",
};

export const BLOCKER_LABEL = {
  [BLOCKER_KIND.AWARD_RATE]: "Award / rate confirmation required",
  [BLOCKER_KIND.AUTHORITY]: "Authority insufficient to price",
  [BLOCKER_KIND.ELIGIBILITY]: "Eligibility facts / statutory conditions unmet",
  [BLOCKER_KIND.SELECTIVE]: "Selective / non-guaranteed",
  [BLOCKER_KIND.SUPERSEDED]: "Superseded program",
  [BLOCKER_KIND.PROHIBITED]: "Prohibited program combination",
  [BLOCKER_KIND.MIN_SPEND]: "Minimum spend not met",
  [BLOCKER_KIND.QUALIFICATION]: "Qualification hard fail",
  [BLOCKER_KIND.DOMINATED]: "Economically dominated (search summary)",
  [BLOCKER_KIND.OTHER]: "Rejected by program rule",
};

export function classifyBlocker(row) {
  const status = row?.candidate_status || "";
  const cls = row?.rejection_reason_class || "";
  const text = String(row?.reason || "");
  let kind = BLOCKER_KIND.OTHER;
  if (status === "DOMINATED_WITH_PROOF") kind = BLOCKER_KIND.DOMINATED;
  else if (cls === "NON_GUARANTEED_SELECTIVE") kind = BLOCKER_KIND.SELECTIVE;
  else if (cls === "SUPERSEDED") kind = BLOCKER_KIND.SUPERSEDED;
  else if (status === "QUALIFICATION_HARD_FAIL") kind = BLOCKER_KIND.QUALIFICATION;
  else if (status === "UNPRICEABLE_AUTHORITY_INSUFFICIENT" || cls === "UNPRICEABLE_AUTHORITY_INSUFFICIENT") {
    if (cls === "UNPRICEABLE_AUTHORITY_INSUFFICIENT") kind = BLOCKER_KIND.AUTHORITY;
    else if (/award condition|rate CEILING|cannot be pre-evaluated|not guaranteed/i.test(text)) kind = BLOCKER_KIND.AWARD_RATE;
    else if (/did not resolve|minimum-spend|eligibility conditions unmet/i.test(text)) kind = BLOCKER_KIND.ELIGIBILITY;
    else kind = BLOCKER_KIND.AUTHORITY;
  } else if (cls === "AUTHORITY_UNRESOLVED_NON_PRICEABLE") {
    kind = /statutory conditions are unmet|conditions unmet/i.test(text) ? BLOCKER_KIND.ELIGIBILITY : BLOCKER_KIND.AUTHORITY;
  } else if (cls === "PAIRWISE_INCOMPATIBLE") kind = BLOCKER_KIND.PROHIBITED;
  else if (cls === "MINIMUM_SPEND_FAIL") kind = BLOCKER_KIND.MIN_SPEND;
  else if (cls === "STATUTORY_CONDITIONS_UNMET") kind = BLOCKER_KIND.ELIGIBILITY;
  else if (cls === "UNRESOLVED_NO_AUTHORITY") kind = BLOCKER_KIND.AUTHORITY;
  return { kind, label: BLOCKER_LABEL[kind], reason: text ? text.replace(/\s+/g, " ").trim() : null };
}

// Hover-length first sentence of the engine's own reason, snake_case humanized.
export function shortBlockerReason(reason) {
  if (!reason) return null;
  const first = String(reason).split(/\.\s/)[0].replace(/\.$/, "");
  return first.replace(/\b[a-z]+(?:_[a-z]+)+\b/g, (t) => t.replace(/_/g, " "));
}
