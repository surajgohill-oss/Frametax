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

// ── JURISDICTION ACCOUNTING (2026-10-02) ─────────────────────────────────────────────────────────────────────────
test("DATA_INCOMPLETE accounted rows are slate (never red, never amber) and any stronger state of the jurisdiction wins", async () => {
  const { buildOptimizerUniverse, OPTIMIZER_STATUS_PRECEDENCE } = await import("../src/lib/globeData.js");
  const row = (code, disposition, extra = {}) => ({
    structure_id: `accounting:${code}`, candidate_status: "NO_PRICEABLE_PROGRAM_MODEL", rejection_reason_class: "DATA_INCOMPLETE",
    primary_jurisdiction: code, participants: [code], disposition, reason: "x", ...extra,
  });
  const allocated = {
    optimizer_scenarios: [], rejection_universe: { first_page: { results: [
      row("BR", "DATA_INCOMPLETE", { missing_facts_reason: "Program/capability data incomplete" }),
      row("SA", "NEEDS_FACTS", { program_name: "Saudi Film Commission Production Rebate", blocker_detail: { kind: "DISCRETIONARY_AWARD_NOT_CONFIRMED", headline: "h" } }),
      row("SA", "DATA_INCOMPLETE"),
    ] }, by_disposition: {} },
  };
  const u = buildOptimizerUniverse(allocated);
  assert.equal(u.get("BR").status, "slate");
  assert.equal(u.get("SA").status, "amber", "needs-facts outranks data-incomplete for the same jurisdiction");
  assert.ok(OPTIMIZER_STATUS_PRECEDENCE.slate < OPTIMIZER_STATUS_PRECEDENCE.red);
});

test("served maximum potential and content gates reach the hover record and the Inspector detail adapters", async () => {
  const d = await import("../src/lib/globeData.js");
  const potential = { maximum_supported_incentive_usd: 2220742.8, potential_npc_usd: 2296944.2, confirmed_incentive_floor_usd: 0 };
  const gates = [{ kind: "SCRIPT_CONTENT_CLEARANCE", status: "NOT_ON_FILE" }];
  const row = { structure_id: "accounting:SA:sa", primary_jurisdiction: "SA", participants: ["SA"], candidate_status: "RULE_REJECTED",
    rejection_reason_class: "STATUTORY_CONDITIONS_UNMET", disposition: "NEEDS_FACTS", incentive_potential: potential, content_gates: gates,
    first_exit_stage: "AUTHORITY_BLOCKED", blocker_detail: { kind: "DISCRETIONARY_AWARD_NOT_CONFIRMED", headline: "h" } };
  assert.deepEqual(d.buildOpportunityDetail(row).incentive_potential, potential);
  assert.deepEqual(d.buildRejectedDetail(row).content_gates, gates);
  assert.equal(d.buildOpportunityDetail(row).first_exit_stage, "AUTHORITY_BLOCKED");
});

test("Project Globe states one representative per jurisdiction and lists accounted needs-facts / data-incomplete jurisdictions", async () => {
  const fs = await import("node:fs");
  const src = fs.readFileSync(new URL("../src/screens/production/ProjectGlobe.jsx", import.meta.url), "utf8");
  assert.match(src, /one representative structure per jurisdiction/);
  assert.match(src, /data-testid="needs-facts-jurisdictions"/);
  assert.match(src, /data-testid="data-incomplete-jurisdictions"/);
  const insp = fs.readFileSync(new URL("../src/shell/Inspector.jsx", import.meta.url), "utf8");
  assert.match(insp, /Maximum potential \(not guaranteed\)/);
  assert.match(insp, /Content, approval and cultural requirements/);
  const hover = fs.readFileSync(new URL("../src/components/GlobeHoverCard.jsx", import.meta.url), "utf8");
  assert.match(hover, /data-blocker-potential/);
});

// ── SINGLE-JURISDICTION COMPLETE SERVED UNIVERSE (2026-10-02) ─────────────────────────────────────────────────────
test("Single-Jurisdiction grouping exposes every served jurisdiction; conditional is never unavailable; winners are a separate stat", async () => {
  const u = await import("../src/lib/jurisdictionUniverse.js");
  const rec = (code, category, extra = {}) => ({ jurisdiction_code: code, category, disposition: category === "LEADING_ALTERNATIVE" ? "EXECUTABLE" : "NEEDS_FACTS", ...extra });
  const allocated = {
    best_per_jurisdiction: { GR: { primary_jurisdiction: "GR" }, MB: { primary_jurisdiction: "CA-MB" } },
    jurisdiction_accounting: { single_jurisdiction_contract: [
      rec("GR", "LEADING_ALTERNATIVE"), rec("CA-MB", "REFERENCE_ALTERNATIVE", { disposition: "EXECUTABLE" }),
      rec("US-TX", "CONDITIONAL_ALTERNATIVE", { potential_rank: 2, missing_conditions: ["award confirmed"] }),
      rec("CA-SK", "CONDITIONAL_ALTERNATIVE", { potential_rank: 1 }),
      rec("AE-DXB", "UNAVAILABLE", { disposition: "HARD_BLOCK" }), rec("BR", "PROGRAM_DATA_INCOMPLETE", { disposition: "DATA_INCOMPLETE" }),
    ] },
  };
  const g = u.groupUniverse(allocated);
  const by = Object.fromEntries(g.groups.map((x) => [x.key, x.items.map((i) => i.jurisdiction_code)]));
  assert.deepEqual(by.CONDITIONAL_ALTERNATIVE, ["CA-SK", "US-TX"], "conditional sorted by potential rank, both visible");
  assert.deepEqual(by.UNAVAILABLE, ["AE-DXB"]);
  assert.deepEqual(by.NOT_SUITABLE_FOR_THIS_PRODUCTION, [], "never populated without a served fit failure");
  assert.deepEqual(by.PROGRAM_DATA_INCOMPLETE, ["BR"]);
  assert.equal(g.total, 6); assert.equal(g.winners, 2); assert.equal(g.unknown.length, 0);
  assert.notEqual(g.total, g.winners);
});

test("co-production opportunities are their own list, labelled as opportunities (never programs), with facts and reasons", async () => {
  const u = await import("../src/lib/jurisdictionUniverse.js");
  assert.equal(u.coproductionNeedsFactsLabel(25), "25 co-production opportunities need facts");
  assert.equal(u.coproductionNeedsFactsLabel(1), "1 co-production opportunity needs facts");
  const rows = u.coproductionRows({ optimizer_opportunities_requiring_facts: [{
    structure_id: "s1", label: "United Kingdom + Canada — official co-production opportunity (uk-ca-bilateral)", classification: "CONDITIONAL_USER_FACT_REQUIRED",
    treaty_resolution_state: "UNRESOLVED_FACTS", blockers: ["no project fact states each party's real ownership/spend share"], ceiling_status: "NOT_ESTABLISHED", is_fully_priced: false,
  }] });
  assert.equal(rows.length, 1);
  assert.equal(rows[0].confirmedFloor, null); assert.equal(rows[0].maximumPotential, null);
  assert.match(rows[0].missingFacts[0], /ownership\/spend share/); assert.match(rows[0].why, /ownership\/spend share/);
});

test("Workspace and Project Globe wire the universe panel and the clickable co-production facts list", async () => {
  const fs = await import("node:fs");
  const ws = fs.readFileSync(new URL("../src/screens/production/Workspace.jsx", import.meta.url), "utf8");
  const pg = fs.readFileSync(new URL("../src/screens/production/ProjectGlobe.jsx", import.meta.url), "utf8");
  assert.match(ws, /<JurisdictionUniversePanel/); assert.match(ws, /<CoproductionFactsList/); assert.match(ws, /coproductionNeedsFactsLabel\(opportunitiesTotal\)/);
  assert.doesNotMatch(ws, /need more facts` : ""/);
  assert.match(pg, /<JurisdictionUniversePanel/); assert.match(pg, /coproductionNeedsFactsLabel\(optimizerProj\.opportunities\.length\)/);
});

// ── LOCATION + CONTENT-GATE WIRING (2026-10-05) ───────────────────────────────────────────────────────────────────
test("content-gate control writes only the served gate key through the project-scoped endpoint, with the three states", async () => {
  const fs = await import("node:fs");
  const insp = fs.readFileSync(new URL("../src/shell/Inspector.jsx", import.meta.url), "utf8");
  const api = fs.readFileSync(new URL("../src/api.js", import.meta.url), "utf8");
  assert.match(api, /postProjectContentGates = \(projectId, gates\)[\s\S]*\/projects\/\$\{projectId\}\/content-gates/);
  for (const v of ["confirmed", "refused", "not_on_file"]) assert.ok(insp.includes(`["${v}"`), v);
  assert.match(insp, /postProjectContentGates\(projectId, \{ \[g\.fact_key\]: control \}\)/, "only the gate's own served fact key is written");
  assert.match(insp, /Advisory risk — disclosed, never a yes\/no eligibility question/);
  assert.match(insp, /<ContentGateControls gates=\{gates\}/);
  const hook = fs.readFileSync(new URL("../src/lib/useCineGlobe.js", import.meta.url), "utf8");
  assert.match(hook, /cineglobe:refetch/);
  const hover = fs.readFileSync(new URL("../src/components/GlobeHoverCard.jsx", import.meta.url), "utf8");
  assert.match(hover, /data-blocker-content-refused/);
});

test("Single-Jurisdiction groups place a confirmed mismatch under NOT SUITABLE and an unconfirmed fit under CONDITIONAL", async () => {
  const u = await import("../src/lib/jurisdictionUniverse.js");
  const mk = (code, category) => ({ jurisdiction_code: code, category, disposition: "EXECUTABLE" });
  const g = u.groupUniverse({ best_per_jurisdiction: {}, jurisdiction_accounting: { single_jurisdiction_contract: [
    mk("AT", "NOT_SUITABLE_FOR_THIS_PRODUCTION"), mk("XX", "CONDITIONAL_ALTERNATIVE"), mk("GR", "LEADING_ALTERNATIVE"),
  ] } });
  const by = Object.fromEntries(g.groups.map((x) => [x.key, x.items.map((i) => i.jurisdiction_code)]));
  assert.deepEqual(by.NOT_SUITABLE_FOR_THIS_PRODUCTION, ["AT"]);
  assert.deepEqual(by.CONDITIONAL_ALTERNATIVE, ["XX"]);
  assert.deepEqual(by.UNAVAILABLE, [], "a mismatch or unknown fit is never Unavailable");
});
