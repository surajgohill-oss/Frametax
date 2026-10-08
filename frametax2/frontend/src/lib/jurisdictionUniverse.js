// COMPLETE SERVED JURISDICTION UNIVERSE (2026-10-02) -- the one pure adapter that turns the backend's
// `allocated_structures.jurisdiction_accounting.single_jurisdiction_contract` into the presentation groups
// Single-Jurisdiction mode (and the Project Globe) must expose. It never computes economics, never re-ranks and never
// invents a category: every value is read verbatim from the served record.
//
// Rules:
//   * Conditional / unknown is never Unavailable.
//   * NOT SUITABLE is shown only for an ESTABLISHED production-fit failure the backend serves (category
//     NOT_SUITABLE_FOR_THIS_PRODUCTION); the group exists but stays empty otherwise.
//   * Program-data-incomplete jurisdictions stay visible in their own explicit section (no fabricated economics).
//   * The jurisdiction-winner count is a DISTINCT statistic (`best_per_jurisdiction`), never the universe size.

import { JURISDICTION_COORDS } from "./jurisdictions.js";

export const UNIVERSE_GROUPS = [
  { key: "LEADING_ALTERNATIVE", label: "Leading alternative" },
  { key: "STRONG_ALTERNATIVE", label: "Strong alternative" },
  { key: "REFERENCE_ALTERNATIVE", label: "Reference alternative" },
  { key: "CONDITIONAL_ALTERNATIVE", label: "Needs facts" },
  { key: "NOT_SUITABLE_FOR_THIS_PRODUCTION", label: "Not suitable" },
  { key: "UNAVAILABLE", label: "Unavailable" },
  { key: "PROGRAM_DATA_INCOMPLETE", label: "Data incomplete" },
];

export const jurisdictionLabel = (rec) => rec?.jurisdiction_name || JURISDICTION_COORDS[rec?.jurisdiction_code]?.name || rec?.jurisdiction_code || "";

export function servedContract(allocated) {
  const c = allocated?.jurisdiction_accounting?.single_jurisdiction_contract;
  return Array.isArray(c) ? c : [];
}

// Winner statistic (executable one-per-jurisdiction representatives) -- distinct from the universe size.
export function winnerCount(allocated) {
  return Object.values(allocated?.best_per_jurisdiction || {}).filter(Boolean).length;
}

const potentialSort = (a, b) =>
  (a.potential_rank ?? Infinity) - (b.potential_rank ?? Infinity) || jurisdictionLabel(a).localeCompare(jurisdictionLabel(b));
const confirmedSort = (a, b) =>
  (a.confirmed_rank ?? Infinity) - (b.confirmed_rank ?? Infinity) || jurisdictionLabel(a).localeCompare(jurisdictionLabel(b));

export function groupUniverse(allocated) {
  const contract = servedContract(allocated);
  const groups = UNIVERSE_GROUPS.map((g) => ({ ...g, items: [] }));
  const byKey = new Map(groups.map((g) => [g.key, g]));
  for (const rec of contract) {
    const g = byKey.get(rec.category);
    if (g) g.items.push(rec); // an unknown category is never silently re-labelled; it is surfaced below
  }
  const known = new Set(UNIVERSE_GROUPS.map((g) => g.key));
  const unknown = contract.filter((r) => !known.has(r.category));
  for (const g of groups) g.items.sort(g.key === "CONDITIONAL_ALTERNATIVE" ? potentialSort : confirmedSort);
  return { groups, unknown, total: contract.length, winners: winnerCount(allocated) };
}

export const universeCounts = (allocated) => {
  const { groups, total, winners, unknown } = groupUniverse(allocated);
  return { total, winners, unclassified: unknown.length, byGroup: Object.fromEntries(groups.map((g) => [g.key, g.items.length])) };
};

// The accounted blocked/conditional row (rejection_universe) behind a contract record -- used to open the SAME Inspector
// every other surface opens for that jurisdiction.
export function accountedRowFor(allocated, rec) {
  const rows = allocated?.rejection_universe?.first_page?.results || [];
  return rows.find((r) => r.primary_jurisdiction === rec.jurisdiction_code && (!rec.program_slug || r.program_slug === rec.program_slug))
    || rows.find((r) => r.primary_jurisdiction === rec.jurisdiction_code && r.candidate_status !== "DOMINATED_WITH_PROOF" && r.candidate_status !== "CO_PRO_OPPORTUNITY")
    || null;
}

export const executableFor = (allocated, rec) => allocated?.best_per_jurisdiction?.[rec.jurisdiction_code] || null;

// Official co-production opportunities that need facts: NOT incentive programs, kept distinct from jurisdiction rows.
export function coproductionRows(allocated) {
  const list = allocated?.optimizer_opportunities_requiring_facts || [];
  return list.map((s) => {
    const missing = [];
    for (const b of s.blockers || []) missing.push(String(b));
    for (const m of s.personnel_missing_facts || []) missing.push(typeof m === "string" ? m : (m.description || m.fact_key || JSON.stringify(m)));
    const established = s.ceiling_status && s.ceiling_status !== "NOT_ESTABLISHED";
    return {
      structure: s,
      id: s.structure_id,
      pairing: s.label || (s.participants || []).join(" + "),
      classification: s.classification || s.candidate_status || "CO_PRO_OPPORTUNITY",
      resolutionState: s.treaty_resolution_state || null,
      missingFacts: missing,
      confirmedFloor: s.is_fully_priced ? (s.confirmed_incentive_floor_usd ?? null) : null,
      maximumPotential: established ? (s.maximum_supported_incentive_usd ?? null) : null,
      why: (s.blockers && s.blockers[0]) || s.reason || "Required project facts are not on file.",
    };
  });
}

export const coproductionNeedsFactsLabel = (n) => `${n} co-production ${n === 1 ? "opportunity needs" : "opportunities need"} facts`;

// MUSIC CARVE-OUT policy-suppressed references (canonical-1.105.0): calculated, priced alternatives the curated
// optimizer surface excludes from preferred presentation (`optimizer_scenarios_music_suppressed`). Read verbatim;
// never ranked into the primary cards, never Leading/Strong.
const codeName = (code) => JURISDICTION_COORDS[code]?.name || code || "";
export function policySuppressedRows(allocated) {
  const list = allocated?.optimizer_scenarios_music_suppressed || [];
  const threshold = allocated?.music_carveout?.threshold_usd ?? null;
  return list.map((s) => {
    const cp = s.music_carveout_counterpart || {};
    const music = (s.component_allocations || []).find((c) => c.component === "music_package");
    const bundled = cp.kind === "CURRENT_LOCATION_BASELINE"
      ? "Music kept at the current location (baseline)"
      : cp.host_component
        ? `Music bundled with ${String(cp.host_component).replace(/_/g, " ")} in ${codeName(cp.host_jurisdiction_code)}`
        : "Not established";
    return {
      structure: s,
      id: s.structure_id,
      route: s.label || (s.participants || []).join(" + "),
      musicDestination: codeName(cp.music_jurisdiction_code || music?.jurisdiction_code),
      bundledRoute: bundled,
      bundledNpc: cp.bundled_npc_with_adjustments_usd ?? null,
      npc: s.npc_with_adjustments_usd ?? null,
      delta: s.music_carveout_delta_usd ?? null,
      threshold: s.music_carveout_threshold_usd ?? threshold,
      status: s.music_carveout_status,
      reason: s.music_carveout_reason || "",
    };
  });
}

export const policySuppressedLabel = (n) =>
  `${n} policy-suppressed reference structure${n === 1 ? "" : "s"}`;
