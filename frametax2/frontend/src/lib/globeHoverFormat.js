// Shared presentation helpers for Globe hover (Phase 3B Batch 1) — plain
// pure functions, no JSX, no React, no fabricated data. Every input here is
// a real field already served by the backend (see globeData.js's
// buildCountryHoverData for where each one is read); this module only
// formats. Future Inspector work should reuse these rather than growing a
// second set of the same formatting logic.

// Full, non-abbreviated currency — deliberately distinct from
// CompactMoney/format.jsx's "$2.6M" style. Phase 3B's hover spec requires
// full precision ("$742,131", never "$742K" or "$0.7M").
export function formatFullUsd(value) {
  if (value === null || value === undefined) return null;
  return `$${Math.round(Number(value)).toLocaleString()}`;
}

export function formatPct(fraction, decimals = 0) {
  if (fraction === null || fraction === undefined) return null;
  return `${(fraction * 100).toFixed(decimals)}%`;
}

// Incentive as a share of GROSS BUDGET — explicitly NOT the statutory/
// modeled program rate (which is a share of qualified spend, a different,
// smaller base). Phase 3B's own spec calls this out: "NOT statutory
// percentage." Returns null rather than a fabricated number when either
// input is missing.
export function incentivePctOfGross(incentiveUsd, grossBudgetUsd) {
  if (incentiveUsd == null || !grossBudgetUsd) return null;
  return formatPct(incentiveUsd / grossBudgetUsd, 1);
}

// The rate that actually funded the incentive/NPC figures shown alongside
// it. CONFIRMED FROM BACKEND SOURCE (allocation_pricing.py): a segment's
// `rate_ceiling` field is populated from `rr.modeled_rate` — literally the
// rate the pricing kernel calls "modeled" and the ONLY rate that feeds
// `incentive_ceiling_usd` / the structure's `selected_incentive_usd` /
// `npc_with_adjustments_usd` (that pipeline is built on `total_ceiling`,
// never `total_floor`). `rate_floor` is the separately-tracked GUARANTEED
// minimum, used only for the conservative NPC uncertainty band — a real,
// different number, not "the same rate under another name."
//
// This is why "Modeled Rate" here reads `rate_ceiling`, not `rate_floor`,
// even though the segment's own field is (confusingly) named "ceiling":
// showing the floor next to a dollar figure the floor didn't produce would
// be a real, if subtle, mismatch between the displayed rate and the
// displayed money — exactly what "do not fabricate" rules out.
export function modeledRateInfo(seg) {
  if (!seg || !seg.claims_incentive || seg.rate_ceiling == null) return null;
  return {
    modeledPct: Math.round(seg.rate_ceiling * 100),
    floorPct: seg.rate_floor != null ? Math.round(seg.rate_floor * 100) : null,
    isBandCeiling: !!seg.is_band_ceiling,
  };
}

// First real sentence of the backend's own discovery-examination `reason`
// string, with raw snake_case requirement tokens humanized (e.g.
// "marine_filming" -> "marine filming"). This is TRUNCATION AND
// REFORMATTING of real backend text, not a fabricated category enum — the
// backend does not expose a structured short-reason-code field (see the
// Phase 3B Batch 1 report's "missing backend contract" note), so a fixed
// taxonomy ("Marine filming" / "Cultural restriction" / ...) would have to
// be guessed from string content, which this deliberately does not do.
export function presentExclusionReason(rawReason) {
  if (!rawReason) return null;
  const firstSentence = rawReason.split(/\.\s/)[0].replace(/\.$/, "");
  return firstSentence.replace(/\b[a-z]+(?:_[a-z]+)+\b/g, (tok) => tok.replace(/_/g, " "));
}

// Related jurisdictions for a Co-Production Opportunity hover: the
// structure's OWN real `participants` list, excluding the jurisdiction
// being hovered. This is the one canonical relationship this data model
// actually has — a broader "who else COULD you partner with" recommendation
// (beyond this structure's own attempted participants) is not something any
// backend field currently expresses; see the Batch 1 report's missing-
// contract note on treaty-partner discovery.
export function relatedJurisdictions(structure, hoveredCode, jurisdictionName) {
  if (!structure?.participants) return [];
  return structure.participants
    .filter((code) => code !== hoveredCode)
    .map((code) => ({ code, name: jurisdictionName(code) }));
}
