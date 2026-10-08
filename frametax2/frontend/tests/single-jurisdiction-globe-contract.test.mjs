import assert from "node:assert/strict";
import test from "node:test";

import {
  buildGlobeView, buildOpportunityDetail,
  buildSingleJurisdictionUniverse,
  SINGLE_JURISDICTION_CATEGORY_SEMANTIC,
} from "../src/lib/globeData.js";

const rec = (code, category, fit, extra = {}) => ({
  jurisdiction_code: code,
  jurisdiction_name: code,
  disposition: category === "REFERENCE_ALTERNATIVE" ? "EXECUTABLE" : "NEEDS_FACTS",
  category,
  confirmed_incentive_usd: null,
  confirmed_npc_usd: null,
  potential_incentive_usd: null,
  potential_npc_usd: null,
  missing_conditions: [],
  production_fit_status: fit,
  production_fit_reasons: [],
  ...extra,
});

const structure = (code) => ({
  structure_id: `winner:${code}`,
  primary_jurisdiction: code,
  participants: [code],
  is_fully_priced: true,
  selected_incentive_usd: 100,
  npc_with_adjustments_usd: 900,
  production_fit_status: "WORKABLE",
  production_fit_reasons: [],
  segments: [],
});

test("Single-Jurisdiction Globe consumes the complete served contract, not only executable winners", () => {
  const contract = [
    rec("GR", "REFERENCE_ALTERNATIVE", "WORKABLE", { confirmed_incentive_usd: 100, confirmed_npc_usd: 900 }),
    rec("US-TX", "CONDITIONAL_ALTERNATIVE", "WORKABLE", { potential_incentive_usd: 310 }),
    rec("CA-SK", "NOT_SUITABLE_FOR_THIS_PRODUCTION", "WEAK", { hard_failure_reason: "Confirmed physical-location mismatch" }),
    rec("FR", "PROGRAM_DATA_INCOMPLETE", "UNKNOWN"),
  ];
  const allocated = {
    structures: [], ranking: [],
    best_per_jurisdiction: { GR: structure("GR") },
    jurisdiction_accounting: { single_jurisdiction_contract: contract },
  };
  const statuses = buildSingleJurisdictionUniverse(allocated);
  assert.equal(statuses.size, contract.length);
  assert.equal(statuses.get("US-TX").status, "amber");
  assert.equal(statuses.get("CA-SK").status, "rose", "Not Suitable is muted rose; Unavailable is the deeper oxblood");
  assert.equal(statuses.get("FR").status, "slate");

  const view = buildGlobeView(allocated, new Map(), { mode: "normal", grossBudgetUsd: 1000 });
  assert.equal(view.polygonColors.size, contract.length);
  assert.equal(view.hoverByIso.get("CA-SK").fullStatusLabel, "Not suitable");
  assert.equal(view.hoverByIso.get("US-TX").contractRecord.jurisdiction_code, "US-TX");
  assert.equal(view.points.length, contract.length);
});

test("every complete-contract category has a declared existing Globe colour", () => {
  for (const [category, semantic] of Object.entries(SINGLE_JURISDICTION_CATEGORY_SEMANTIC)) {
    assert.match(semantic.hex, /^#[0-9a-f]{6}$/i, category);
    assert.ok(semantic.label, category);
  }
});

test("conditional/unavailable Inspector adapters retain the same served production fit", () => {
  const detail = buildOpportunityDetail({
    primary_jurisdiction: "CA-SK", disposition: "NEEDS_FACTS",
    production_fit_status: "WEAK", production_fit_reasons: ["CA-SK:MARINE_MISMATCH"],
    production_fit_legs: ["CA-SK"], production_fit_soft_signals: { matched: ["CA-SK:rural"] },
    production_fit_capability_evidence: [{ jurisdiction: "CA-SK", token: "rural" }],
  });
  assert.equal(detail.production_fit_status, "WEAK");
  assert.deepEqual(detail.production_fit_reasons, ["CA-SK:MARINE_MISMATCH"]);
  assert.deepEqual(detail.production_fit_legs, ["CA-SK"]);
});
