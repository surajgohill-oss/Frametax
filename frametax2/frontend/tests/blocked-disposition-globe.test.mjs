// Shared jurisdiction disposition on the Globe: RED only for a served HARD_BLOCK; NEEDS_FACTS blocked rows and
// executable alternatives conditional on missing capability data are AMBER; everything else valid is SLATE.
import test from "node:test";
import assert from "node:assert/strict";
import { buildOptimizerUniverse, globeKey } from "../src/lib/globeData.js";
import { alternativeLabel } from "../src/lib/alternativeLabels.js";

const row = (primary, extra) => ({ structure_id: `r-${primary}`, primary_jurisdiction: primary, participants: [primary], candidate_status: "UNPRICEABLE_AUTHORITY_INSUFFICIENT", ...extra });
const allocated = (rows, evaluated = []) => ({
  recommended_optimizer_options: [], evaluated_optimizer_alternatives: evaluated, optimizer_opportunities_requiring_facts: [],
  rejection_universe: { first_page: { results: rows }, by_disposition: {} },
});

test("a NEEDS_FACTS blocked row is AMBER with its exact reason; a HARD_BLOCK is RED with its hard-block reason", () => {
  const u = buildOptimizerUniverse(allocated([
    row("US-TX", { disposition: "NEEDS_FACTS", missing_facts_reason: "award condition(s) [us-tx-award-allocation-required] cannot be pre-evaluated", reason: "x" }),
    row("AE-DXB", { candidate_status: "FEASIBILITY_REVIEW_REQUIRED", rejection_reason_class: "SUPERSEDED", disposition: "HARD_BLOCK", hard_block_reason: "The program is superseded" }),
  ]));
  assert.equal(u.get("US-TX").status, "amber");
  assert.match(u.get("US-TX").meta.reason, /us-tx-award-allocation-required/);
  assert.equal(u.get(globeKey("AE-DXB")).status, "red");
  assert.match(u.get(globeKey("AE-DXB")).meta.reason, /superseded/);
});

test("every red entry carries a hard-block reason; no NEEDS_FACTS row is ever red", () => {
  const rows = [
    row("A", { disposition: "NEEDS_FACTS", missing_facts_reason: "m" }),
    row("B", { disposition: "NEEDS_FACTS", missing_facts_reason: "m" }),
    row("C", { disposition: "HARD_BLOCK", hard_block_reason: "h" }),
  ];
  const u = buildOptimizerUniverse(allocated(rows));
  const red = [...u.values()].filter((e) => e.status === "red");
  assert.equal(red.length, 1);
  assert.ok(red.every((e) => e.meta.reason));
  assert.ok(["A", "B"].every((k) => u.get(k).status === "amber"));
});

test("executable alternatives: missing-capability actionability is AMBER, everything else valid stays SLATE", () => {
  const ev = (id, code, extra) => ({ structure_id: id, economic_identity: id, candidate_status: "PRICED", is_fully_priced: true, participants: [code], primary_jurisdiction: code, recommendation_status: "EVALUATED_ALTERNATIVE", ...extra });
  const u = buildOptimizerUniverse(allocated([], [
    ev("e1", "CA-MB", { actionability: "AMBER", actionability_reason: "MISSING_LOCATION_CAPABILITY_DATA: DESERT_ENVIRONMENTS_NOT_ASSESSABLE" }),
    ev("e2", "GR", { actionability: "SLATE" }),
    ev("e3", "IT", {}),
  ]));
  assert.equal(u.get("CA-MB").status, "amber");
  assert.match(u.get("CA-MB").meta.reason, /MISSING_LOCATION_CAPABILITY_DATA/);
  assert.equal(u.get("GR").status, "silver");
  assert.equal(u.get("IT").status, "silver");
});

test("a blocked row classified NEEDS_FACTS reads NEEDS MORE FACTS, never UNAVAILABLE", () => {
  assert.equal(alternativeLabel({ candidate_status: "FEASIBILITY_REVIEW_REQUIRED", disposition: "NEEDS_FACTS" }), "NEEDS MORE FACTS");
  assert.equal(alternativeLabel({ candidate_status: "FEASIBILITY_REVIEW_REQUIRED", disposition: "HARD_BLOCK" }), "UNAVAILABLE");
});
