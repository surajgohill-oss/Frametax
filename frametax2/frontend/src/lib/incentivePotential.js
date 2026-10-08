// MAXIMUM-POTENTIAL INCENTIVE CONTRACT (2026-10-01) -- the ONE frontend reader of the
// backend-served confirmed-floor / maximum-supported incentive contract
// (backend/app/services/incentive_potential.py). Workspace cards, the structure Inspector
// and the Globe adapter all call this; it performs NO arithmetic and no inference -- every
// number is a served field passed through verbatim, so every surface shows the same value
// by construction.

export const CERTAINTY_LABEL = {
  CONFIRMED: "Confirmed",
  CONDITIONAL: "Conditional",
  REFERENCE_ONLY: "Reference only",
};

export function readIncentivePotential(structure) {
  if (!structure || typeof structure !== "object") return null;
  if (structure.ceiling_status === undefined && structure.confirmed_incentive_floor_usd === undefined) return null;
  return {
    confirmedIncentive: structure.confirmed_incentive_floor_usd ?? null,
    maxIncentive: structure.maximum_supported_incentive_usd ?? null,
    confirmedNpc: structure.confirmed_npc_usd ?? null,
    potentialNpc: structure.potential_npc_usd ?? null,
    upside: structure.potential_upside_usd ?? null,
    ceilingStatus: structure.ceiling_status ?? null,
    certainty: structure.economics_certainty ?? null,
    missingFacts: Array.isArray(structure.ceiling_missing_facts) ? structure.ceiling_missing_facts : [],
    basis: structure.ceiling_basis ?? null,
    confirmedRank: structure.confirmed_financial_rank ?? null,
    potentialRank: structure.potential_opportunity_rank ?? null,
  };
}

export function certaintyLabel(pot) {
  return (pot && CERTAINTY_LABEL[pot.certainty]) || "Reference only";
}

// Precise, two-axis economics statement for the Inspector: the confirmed floor and the unresolved upside are
// different facts, so the whole structure is never labelled "Conditional" merely because its maximum needs facts.
// Served fields only (certainty = confidence in the confirmed floor / award; ceilingStatus = the upside axis).
export function economicsStatusText(pot) {
  if (!pot) return "Reference only";
  if (pot.certainty === "REFERENCE_ONLY") return "Reference only";
  if (pot.ceilingStatus === "NOT_ESTABLISHED") return "Confirmed floor · maximum not established";
  if (pot.ceilingStatus === "CONDITIONAL") return "Confirmed floor · maximum needs the facts below";
  if (pot.certainty === "CONDITIONAL") return "Maximum equals the confirmed floor · award confirmation open";
  return "Confirmed";
}

// One-line summary of what is missing for the maximum, for the dense card. The full list is
// always available through `missingFactsTitle` (tooltip) and the Inspector.
export function missingFactsSummary(pot, max = 2) {
  if (!pot) return "";
  if (pot.ceilingStatus === "NOT_ESTABLISHED") return "Maximum not established";
  if (pot.ceilingStatus !== "CONDITIONAL") {
    // Maximum equals the confirmed floor. When the structure is still CONDITIONAL it is for a
    // different reason (discretionary / preapproval / legal-review risk), never missing upside facts.
    return pot.certainty === "CONDITIONAL" ? "Max = confirmed · award risk open" : "No conditional upside";
  }
  const names = pot.missingFacts.map((f) => f.description).filter(Boolean);
  if (names.length === 0) return "Maximum requires confirmation";
  const shown = names.slice(0, max).join(" · ");
  return names.length > max ? `${shown} +${names.length - max} more` : shown;
}

export function missingFactsTitle(pot) {
  if (!pot || !pot.missingFacts.length) return undefined;
  return pot.missingFacts
    .map((f) => `${f.jurisdiction_code || ""} ${f.program_slug || ""}: ${f.description}${f.state ? ` [${f.state}]` : ""}`.trim())
    .join("\n");
}

// Display rows for the shared contract, in one fixed order, used by every compact surface
// (Globe hover, segment Inspector). Values are the served fields verbatim -- a null stays null.
export function potentialRows(pot) {
  if (!pot) return [];
  return [
    { key: "confirmedIncentive", label: "Confirmed incentive", value: pot.confirmedIncentive },
    { key: "maxIncentive", label: "Max potential incentive", value: pot.maxIncentive },
    { key: "confirmedNpc", label: "Confirmed NPC", value: pot.confirmedNpc },
    { key: "potentialNpc", label: "Potential NPC", value: pot.potentialNpc },
  ];
}

// ATTAINABILITY (2026-10-08): how reachable the maximum is, stated from the served facts only -- separate from the
// structure's category, which is never relabelled "conditional". `awardRisk` is the shared administrative/award-risk
// disclosure (an approval step). Returns { headline, requirement, more }:
//   headline    "Maximum confirmed from known facts" | "Maximum requires 1 approval" | "Maximum requires 2 facts" | ...
//   requirement the first unresolved requirement (first clause of the served description), or null
//   more        how many further served requirements are left to the Inspector
export function attainability(pot, awardRisk = false) {
  if (!pot) return { headline: "Maximum not established", requirement: null, more: 0 };
  if (pot.ceilingStatus === "NOT_ESTABLISHED") return { headline: "Maximum not established from known facts", requirement: null, more: 0 };
  const missing = Array.isArray(pot.missingFacts) ? pot.missingFacts : [];
  if (pot.ceilingStatus !== "CONDITIONAL") {
    const open = awardRisk || pot.certainty === "CONDITIONAL";
    return open
      ? { headline: "Maximum requires 1 approval", requirement: "Award confirmation", more: 0 }
      : { headline: "Maximum confirmed from known facts", requirement: null, more: 0 };
  }
  const approvals = missing.filter((f) => f.state === "AUTHORITY_UNRESOLVED").length + (awardRisk && !missing.some((f) => f.state === "AUTHORITY_UNRESOLVED") ? 1 : 0);
  const facts = missing.filter((f) => f.state !== "AUTHORITY_UNRESOLVED").length;
  const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
  const parts = [approvals ? plural(approvals, "approval") : null, facts ? plural(facts, "fact") : null].filter(Boolean);
  const first = missing.map((f) => f.description).find(Boolean);
  return {
    headline: parts.length ? `Maximum requires ${parts.join(" and ")}` : "Maximum requires confirmation",
    // first clause of the served description, with any rate/percentage removed from the card face (rates stay in the Inspector)
    requirement: first
      ? String(first).split(/ -- | — | \(/)[0].replace(/[+\-−]?\s?\d+(?:\.\d+)?\s?%\s*/g, "").replace(/^[\s+]+/, "").trim() || "Additional approval or fact"
      : (awardRisk ? "Award confirmation" : null),
    more: Math.max(0, missing.length - 1),
  };
}
