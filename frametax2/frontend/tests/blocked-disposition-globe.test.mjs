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

// ── exact program blocker (2026-10-02) ───────────────────────────────────────────────────────────
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { optimizerProjection } from "../src/lib/workspaceScenarioMode.js";
import { buildOpportunityDetail, buildRejectedDetail, buildCountryHoverData } from "../src/lib/globeData.js";
const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");

const detail = { headline: "Creative Saskatchewan is a discretionary award", guaranteed_floor: "none", potential_ceiling_rate: 0.3,
  unresolved_propositions: [{ condition_id: "c", description: "stream", fact_key: null, stored_value: null }] };

test("the exact blocker detail reaches the universe, hover record and both Inspector detail builders", () => {
  const sk = row("CA-SK", { disposition: "NEEDS_FACTS", missing_facts_reason: detail.headline, blocker_detail: detail, program_name: "Creative Saskatchewan" });
  const u = buildOptimizerUniverse(allocated([sk]));
  const entry = u.get(globeKey("CA-SK"));
  assert.equal(entry.meta.detail, detail);
  const hover = buildCountryHoverData(u, 1_000_000, "optimizer").get(globeKey("CA-SK"));
  assert.equal(hover.blockerDetail, detail);
  assert.equal(buildOpportunityDetail(sk).blocker_detail, detail);
  assert.equal(buildRejectedDetail(sk).blocker_detail, detail);
});

test("NOT_APPLICABLE rows are neither red nor amber", () => {
  const na = row("CZ", { disposition: "NOT_APPLICABLE", candidate_status: "FEASIBILITY_REVIEW_REQUIRED" });
  const p = optimizerProjection(allocated([na]));
  assert.equal(p.rejected.length, 0);
  assert.equal(p.needsFactsBlocked.length, 0);
  assert.equal(buildOptimizerUniverse(allocated([na])).size, 0);
});

test("Inspector and hover render the exact blocker through one section / one block, with no client logic", () => {
  const insp = readFileSync(join(SRC, "shell", "Inspector.jsx"), "utf8");
  assert.equal((insp.match(/<BlockerDetailSection detail=\{data\.blocker_detail\}/g) || []).length, 2, "needs-facts and unavailable Inspectors");
  assert.match(insp, /Unresolved propositions \(what unlocks the ceiling\)/);
  assert.match(insp, /not on file/);
  assert.match(readFileSync(join(SRC, "components", "GlobeHoverCard.jsx"), "utf8"), /data-blocker-detail/);
});

test("an AMBER executable alternative opens the structure Inspector; only an unpriced row opens the needs-facts one", () => {
  const ws = readFileSync(join(SRC, "screens", "production", "Workspace.jsx"), "utf8");
  assert.match(ws, /if \(s\.is_fully_priced\) openInspector\("candidate-structure", buildCandidateDetail\(s\)\);\s*else openInspector\("optimizer-opportunity"/);
  const pg = readFileSync(join(SRC, "screens", "production", "ProjectGlobe.jsx"), "utf8");
  assert.match(pg, /pt\.sourceStructure\.is_fully_priced \? selectStructure\(pt\.sourceStructure\) : selectOpportunity/);
});
