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
