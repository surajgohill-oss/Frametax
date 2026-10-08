// MAXIMUM-POTENTIAL INCENTIVE CONTRACT (2026-10-01): Workspace cards and the structure
// Inspector render the backend-served confirmed/maximum fields verbatim, through one shared
// reader, with no client recomputation.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { buildCandidateDetail } from "../src/lib/globeData.js";
import {
  readIncentivePotential, certaintyLabel, missingFactsSummary, missingFactsTitle,
} from "../src/lib/incentivePotential.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

const served = {
  structure_id: "s1", economic_identity: "e1", classification: "HYBRID_ANCHOR_COMPONENT",
  primary_jurisdiction: "MU", participants: ["MU", "CA-MB"], is_fully_priced: true,
  candidate_status: "PRICED", selected_incentive_usd: 1318553.7, npc_with_adjustments_usd: 3775139.3,
  segments: [], component_allocations: [],
  // deliberately NOT internally consistent with anything a client could derive:
  confirmed_incentive_floor_usd: 111, maximum_supported_incentive_usd: 222,
  confirmed_npc_usd: 333, potential_npc_usd: 444, potential_upside_usd: 555,
  ceiling_status: "CONDITIONAL", economics_certainty: "CONDITIONAL",
  ceiling_missing_facts: [
    { fact_id: "a", description: "Frequent Filming Bonus (10%)", state: "USER_FACT_REQUIRED", jurisdiction_code: "CA-MB", program_slug: "mb" },
    { fact_id: "b", description: "Authority approval of the up-to rate", state: "AUTHORITY_UNRESOLVED", jurisdiction_code: "CA-MB", program_slug: "mb" },
    { fact_id: "c", description: "Third fact", state: "AUTHORITY_UNRESOLVED", jurisdiction_code: "CA-MB", program_slug: "mb" },
  ],
  ceiling_basis: { method: "SEGMENT_TIERS", legs: [] },
  confirmed_financial_rank: 7, potential_opportunity_rank: 2,
};

test("the shared reader passes served values through verbatim -- no recomputation", () => {
  const p = readIncentivePotential(served);
  assert.equal(p.confirmedIncentive, 111);
  assert.equal(p.maxIncentive, 222);
  assert.equal(p.confirmedNpc, 333);
  assert.equal(p.potentialNpc, 444);
  assert.equal(p.upside, 555);
  assert.equal(p.confirmedRank, 7);
  assert.equal(p.potentialRank, 2);
  assert.equal(certaintyLabel(p), "Conditional");
});

test("Inspector detail and Workspace card read the identical contract", () => {
  const detail = buildCandidateDetail(served);
  assert.deepEqual(detail.incentive_potential, readIncentivePotential(served));
});

test("missing facts are summarised from the served list, with the full list in the tooltip", () => {
  const p = readIncentivePotential(served);
  assert.equal(missingFactsSummary(p), "Frequent Filming Bonus (10%) · Authority approval of the up-to rate +1 more");
  assert.match(missingFactsTitle(p), /CA-MB mb: Third fact \[AUTHORITY_UNRESOLVED\]/);
});

test("absent / unestablished contract is disclosed, never fabricated", () => {
  assert.equal(readIncentivePotential({ structure_id: "legacy" }), null);
  const p = readIncentivePotential({ ceiling_status: "NOT_ESTABLISHED", economics_certainty: "CONFIRMED",
    confirmed_incentive_floor_usd: 5, confirmed_npc_usd: 9 });
  assert.equal(p.maxIncentive, null);
  assert.equal(p.potentialNpc, null);
  assert.equal(missingFactsSummary(p), "Maximum not established");
  const confirmed = readIncentivePotential({ ceiling_status: "CONFIRMED", economics_certainty: "CONFIRMED",
    confirmed_incentive_floor_usd: 5, maximum_supported_incentive_usd: 5, confirmed_npc_usd: 9, potential_npc_usd: 9 });
  assert.equal(missingFactsSummary(confirmed), "No conditional upside");
  // maximum == confirmed but the structure is conditional for another reason (award risk)
  const award = readIncentivePotential({ ceiling_status: "CONFIRMED", economics_certainty: "CONDITIONAL",
    confirmed_incentive_floor_usd: 5, maximum_supported_incentive_usd: 5, confirmed_npc_usd: 9, potential_npc_usd: 9 });
  assert.equal(missingFactsSummary(award), "Max = confirmed · award risk open");
  assert.equal(certaintyLabel(readIncentivePotential({ ceiling_status: "NOT_ESTABLISHED", economics_certainty: "REFERENCE_ONLY" })), "Reference only");
});

test("Workspace card and Inspector use the shared reader and perform no arithmetic on the contract", () => {
  // the card's economic well is the shared component Workspace and Overview both render
  const ws = read("screens/production/Workspace.jsx") + read("components/EconomicWell.jsx");
  const insp = read("shell/Inspector.jsx");
  assert.match(ws, /readIncentivePotential\(structure\)/);
  assert.match(read("screens/production/Workspace.jsx"), /<EconomicWell pot=\{pot\}/);
  // Card labels (economic card interior v2, 2026-10-08): maximum-potential NPC leads, confirmed NPC beneath it.
  assert.match(ws, /Maximum-potential NPC/);
  assert.match(ws, /Maximum-potential incentive/);
  assert.match(ws, /Confirmed NPC/);
  assert.match(ws, /Confirmed incentive/);
  assert.match(ws, /MFNI ADJUSTMENT NOT YET MODELED/);
  assert.match(ws, /NPC AFTER MFNI/);
  assert.match(ws, /Assumptions editing not yet available/);
  assert.match(insp, /Max potential incentive/);
  assert.match(insp, /Needed to reach the maximum/);
  for (const [name, text] of [["Workspace", ws], ["Inspector", insp]]) {
    assert.doesNotMatch(
      text,
      /(pot|incentive_potential)\.(maxIncentive|potentialNpc|confirmedNpc|confirmedIncentive|upside)\s*[-+*/]/,
      `${name} must not do arithmetic on the served contract`,
    );
  }
  const reader = read("lib/incentivePotential.js");
  assert.doesNotMatch(reader, /[a-zA-Z_.)\]]\s[-*/]\s[a-zA-Z_(]/.source ? /\b(maxIncentive|potentialNpc)\s*[-*/]/ : /x/);
});

// ── Globe hover + segment Inspector (completion of 6240e09) ──────────────────────────────────
import { buildCountryHoverData } from "../src/lib/globeData.js";
import { MODE_NORMAL, MODE_OPTIMIZER } from "../src/lib/workspaceScenarioMode.js";
import { structureStatusDetail } from "../src/lib/alternativeLabels.js";
import { potentialRows } from "../src/lib/incentivePotential.js";

test("Globe hover record carries the SAME shared contract as the card (both modes), verbatim", () => {
  const entry = { status: "jade", hex: "#000", best: { structure: served, code: "MU" } };
  for (const mode of [MODE_NORMAL, MODE_OPTIMIZER]) {
    const hover = buildCountryHoverData(new Map([["MU", entry]]), 4_000_000, mode).get("MU");
    assert.deepEqual(hover.incentivePotential, readIncentivePotential(served));
  }
  const unpriced = { ...served, is_fully_priced: false };
  const h2 = buildCountryHoverData(new Map([["MU", { ...entry, best: { structure: unpriced, code: "MU" } }]]), 1, MODE_NORMAL).get("MU");
  assert.equal(h2.incentivePotential, null, "an unpriced structure never shows maximum economics");
});

test("segment Inspector context carries the structure's shared contract (Map/Split/Globe openers)", () => {
  assert.deepEqual(structureStatusDetail(served, null).incentive_potential, readIncentivePotential(served));
  assert.equal(structureStatusDetail({ structure_id: "legacy" }, null).incentive_potential, undefined);
  assert.deepEqual(potentialRows(readIncentivePotential(served)).map((r) => r.value), [111, 222, 333, 444]);
});

test("hover bodies and every segment-Inspector opener render the shared contract, never a recompute", () => {
  const hover = read("components/GlobeHoverCard.jsx");
  assert.equal((hover.match(/<PotentialFields pot=/g) || []).length, 4,
    "the three priced structure bodies plus the complete-contract jurisdiction body");
  assert.match(hover, /hidePotential=\{!!hover\.structureDetail\?\.incentive_potential\}/, "a route hover renders the contract once");
  assert.doesNotMatch(hover, /pot\.\w+\s*[-+*/]\s*pot\./);
  const insp = read("shell/Inspector.jsx");
  assert.equal((insp.match(/<IncentivePotentialRows pot=\{data\.incentive_potential\}/g) || []).length, 2, "structure + segment Inspector");
  assert.equal((insp.match(/<NeededForMaximum pot=\{data\.incentive_potential\}/g) || []).length, 2);
  assert.equal((read("screens/production/Workspace.jsx").match(/\.\.\.structureStatusDetail\(/g) || []).length, 2);
  for (const f of ["screens/production/Scenarios.jsx", "screens/production/Overview.jsx"]) {
    assert.match(read(f), /incentive_potential: readIncentivePotential\(s\)/);
  }
});

// ── Precise structure wording (2026-10-08): the unresolved upside is its own axis ────────────────
import { economicsStatusText } from "../src/lib/incentivePotential.js";

test("economicsStatusText never labels a whole structure 'Conditional' for an unresolved upside", () => {
  const pot = (o) => readIncentivePotential({ ceiling_status: "CONFIRMED", economics_certainty: "CONFIRMED", confirmed_incentive_floor_usd: 5, ...o });
  assert.equal(economicsStatusText(pot({})), "Confirmed");
  assert.equal(economicsStatusText(pot({ ceiling_status: "CONDITIONAL", economics_certainty: "CONDITIONAL" })), "Confirmed floor · maximum needs the facts below");
  assert.equal(economicsStatusText(pot({ ceiling_status: "NOT_ESTABLISHED" })), "Confirmed floor · maximum not established");
  assert.equal(economicsStatusText(pot({ economics_certainty: "CONDITIONAL" })), "Maximum equals the confirmed floor · award confirmation open");
  assert.equal(economicsStatusText(pot({ economics_certainty: "REFERENCE_ONLY" })), "Reference only");
  for (const o of [{}, { ceiling_status: "CONDITIONAL", economics_certainty: "CONDITIONAL" }, { ceiling_status: "NOT_ESTABLISHED" }]) {
    assert.doesNotMatch(economicsStatusText(pot(o)), /^Conditional$/);
  }
});

test("Inspector, universe panel and Globe state the same served jurisdiction category and reason", () => {
  const univ = read("components/JurisdictionUniverse.jsx");
  const insp = read("shell/Inspector.jsx");
  // every Inspector kind opened from the universe/Globe carries the served category + reason
  assert.equal((univ.match(/\.\.\.category/g) || []).length, 3, "candidate, rejection and opportunity Inspectors all receive the category");
  assert.match(insp, /data-jurisdiction-category/);
  assert.equal((insp.match(/<JurisdictionCategoryDisclosure data=\{data\} \/>/g) || []).length, 3);
  // the row never appends the lowercased certainty word to a whole jurisdiction
  assert.doesNotMatch(univ, /economic_certainty\)\.toLowerCase\(\)/);
  // the Globe adapter reads the served upside axis instead of inferring it from certainty
  assert.match(read("lib/globeData.js"), /ceiling_status: rec\.ceiling_status \?\?/);
});

// ── Economic card interior v2: attainability, no percentages, no whole-structure CONDITIONAL ──────
import { attainability } from "../src/lib/incentivePotential.js";

test("attainability states how reachable the maximum is from served facts, never labelling the structure conditional", () => {
  const pot = (o) => readIncentivePotential({ ceiling_status: "CONFIRMED", economics_certainty: "CONFIRMED", confirmed_incentive_floor_usd: 5, ...o });
  assert.equal(attainability(pot({})).headline, "Maximum confirmed from known facts");
  assert.equal(attainability(pot({ economics_certainty: "CONDITIONAL" })).headline, "Maximum requires 1 approval");
  assert.equal(attainability(pot({ ceiling_status: "NOT_ESTABLISHED" })).headline, "Maximum not established from known facts");
  const facts = [
    { fact_id: "a", description: "+10% Frequent Filming + 5% Manitoba Producer -- needs production history", state: "USER_FACT_REQUIRED" },
    { fact_id: "b", description: "Film board approval", state: "AUTHORITY_UNRESOLVED" },
    { fact_id: "c", description: "Shoot location confirmation", state: "USER_FACT_REQUIRED" },
  ];
  const a = attainability(pot({ ceiling_status: "CONDITIONAL", ceiling_missing_facts: facts }));
  assert.equal(a.headline, "Maximum requires 1 approval and 2 facts");
  assert.equal(a.more, 2);
  assert.doesNotMatch(a.requirement, /%/, "no rate or percentage on the card face");
  for (const o of [{}, { economics_certainty: "CONDITIONAL" }, { ceiling_status: "CONDITIONAL", ceiling_missing_facts: facts }]) {
    assert.doesNotMatch(attainability(pot(o)).headline, /conditional/i);
  }
});

test("economic card interior: one shared well, no gross budget / rate / CONDITIONAL on either card face", () => {
  const well = read("components/EconomicWell.jsx");
  const ws = read("screens/production/Workspace.jsx");
  const ov = read("components/IncentiveIntelligence.jsx");
  assert.doesNotMatch(well + ws + ov, /Gross budget/i.test(ws) ? /x^/ : /Gross budget/, "Gross budget is never printed inside a card");
  assert.doesNotMatch(ov, /compactIncentiveRate|rateLine|Vs\. current/, "no rate/percentage line on the Overview card face");
  assert.doesNotMatch(read("lib/productionOptions.js").match(/export function cardStatus[\s\S]*?\n}\n/)[0], /return "CONDITIONAL"/);
  // order: maximum-potential NPC, confirmed NPC, incentives, bar, MFNI, attainability
  const order = ["Maximum-potential NPC", "Confirmed NPC", "Confirmed incentive", "wsx-bar", "wsx-econ-mfni", "wsx-econ-need"].map((s) => well.indexOf(s));
  assert.deepEqual(order, [...order].sort((x, y) => x - y));
  assert.ok(order.every((i) => i >= 0));
  // Workspace: qualified spend only after the well
  assert.ok(ws.indexOf("<EconomicWell") < ws.indexOf('className="wsx-qs"'));
});
