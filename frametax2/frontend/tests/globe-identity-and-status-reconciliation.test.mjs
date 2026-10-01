// GLOBE_WIRING_REMEDIATION (2026-10-01) -- focused regression lock for the
// shared Optimizer Globe defects found by an automated four-project inventory:
//   * four served jurisdictions (IN, PE, CA-SK, KZ) had NO coordinate/name entry,
//     so their polygons coloured but no marker/hover/click target existed;
//   * three-globe keys html/beacon objects by array index, so factories that
//     close over the datum served STALE identity after the marker list changed;
//   * the route's own markers overwrote a jurisdiction's underlying category;
//   * DOMINATED_WITH_PROOF search aggregates / aggregated rule-rejected
//     permutations were presented as blocked structures (e.g. "Rejected (525,882)");
//   * blocked jurisdictions carried one unexplained red state.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { buildGlobeView, buildOptimizerUniverse, globeKey } from "../src/lib/globeData.js";
import { optimizerProjection } from "../src/lib/workspaceScenarioMode.js";
import { JURISDICTION_COORDS } from "../src/lib/jurisdictions.js";
import { classifyBlocker, BLOCKER_KIND } from "../src/lib/blockerDisposition.js";

const readSrc = (rel) => readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "src", rel), "utf8");

// Every jurisdiction code actually served by the four acceptance productions
// (Little Utopia, F#K Valentine's Day, Bad Hombres, Lips Like Sugar).
const SERVED_CODES = ["AE-DXB","AL","AT","AU","AU-NSW","AU-QLD","AU-SA","BE","BG","CA","CA-AB","CA-BC","CA-MB","CA-NB","CA-NL","CA-NS","CA-ON","CA-QC","CA-SK","CH","CL","CO","CR","CY","CZ","DE","DK","DO","EE","EG","ES","FI","FJ","FR","GB","GE","GH","GR","HR","HU","IE","IN","IS","IT","JO","JP","KR","KZ","LT","LV","MA","ME","MK","MN","MT","MU","MX","MY","NZ","PA","PE","PL","PT","QA","RO","RS","SE","SG","SI","SK","TH","TT","UA","US-AL","US-AZ","US-CA","US-CO","US-CT","US-GA","US-HI","US-IL","US-KY","US-LA","US-MA","US-MD","US-MN","US-MS","US-NC","US-NM","US-NV","US-NY","US-OK","US-OR","US-PA","US-PR","US-RI","US-SC","US-TN","US-TX","US-UT","US-VA","UY","UZ","ZA"];

function cand(id, participants, overrides = {}) {
  return {
    structure_id: id, economic_identity: `econ-${id}`, classification: "HYBRID_ANCHOR_COMPONENT",
    primary_jurisdiction: participants[0], participants, label: `${id} label`,
    npc_with_adjustments_usd: 1_000_000, selected_incentive_usd: 300_000, is_fully_priced: true,
    practicality_tier: "PRACTICAL_HYBRID", recommendation_status: "EVALUATED_ALTERNATIVE", is_recommended: false,
    savings_vs_current_usd: 50_000, segments: [], component_allocations: [], ...overrides,
  };
}
function row(id, status, participants, extra = {}) {
  return { structure_id: id, name: `${id} row`, candidate_status: status, participants, primary_jurisdiction: participants[0], ...extra };
}
function alloc({ recommended = [], evaluated = [], opportunities = [], rows = [], byDisp = null }) {
  const bd = byDisp || rows.reduce((a, r) => ({ ...a, [r.candidate_status]: (a[r.candidate_status] || 0) + 1 }), {});
  return {
    structures: [], ranking: [], best_per_jurisdiction: {},
    recommended_optimizer_options: recommended, recommended_optimizer_options_total: recommended.length,
    evaluated_optimizer_alternatives: evaluated, evaluated_optimizer_alternatives_total: evaluated.length,
    optimizer_opportunities_requiring_facts: opportunities, optimizer_opportunities_requiring_facts_total: opportunities.length,
    optimizer_executable_total: recommended.length + evaluated.length,
    rejection_universe: { total_count: rows.length, by_disposition: bd, first_page: { results: rows } },
  };
}

test("every served jurisdiction code has coordinates and its own human name (no marker-less polygons)", () => {
  const missing = SERVED_CODES.filter((c) => !JURISDICTION_COORDS[c]);
  assert.deepEqual(missing, [], "served codes without a marker coordinate");
  for (const c of SERVED_CODES) {
    assert.ok(JURISDICTION_COORDS[c].name && JURISDICTION_COORDS[c].name !== c, `${c} needs a real name`);
  }
  assert.equal(JURISDICTION_COORDS["CA-SK"].name, "Saskatchewan");
});

test("strongest status wins: recommended > evaluated > needs facts > blocked; a blocked row never downgrades an evaluated jurisdiction", () => {
  const a = alloc({
    recommended: [cand("rec", ["GR", "IT"], { recommendation_status: "RECOMMENDED", is_recommended: true })],
    evaluated: [cand("ev", ["CA-MB", "IE"])],
    opportunities: [row("opp", "CO_PRO_OPPORTUNITY", ["IE", "AU"], { reason: "Partner facts required" })],
    rows: [
      row("blk-mb", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", ["CA-MB"], { rejection_reason_class: "PRICING_BLOCKED", reason: "CA-MB/x: rate CEILING (31%) award condition(s) [up-to] cannot be pre-evaluated." }),
      row("blk-au", "FEASIBILITY_REVIEW_REQUIRED", ["AU"], { rejection_reason_class: "NON_GUARANTEED_SELECTIVE", reason: "selective" }),
      row("blk-tx", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", ["US-TX"], { rejection_reason_class: "PRICING_BLOCKED", reason: "US-TX/miip: the program states only a rate CEILING (31%) with no guaranteed floor tier, and its award condition(s) [x] cannot be pre-evaluated." }),
    ],
  });
  const u = buildOptimizerUniverse(a);
  assert.equal(u.get("GR").status, "gold");
  assert.equal(u.get("IT").status, "gold");
  assert.equal(u.get("CA-MB").status, "silver", "blocked row must not turn an evaluated jurisdiction red");
  assert.equal(u.get("CA-MB").counts.blocked, 1);
  assert.equal(u.get("CA-MB").counts.evaluated, 1);
  assert.equal(u.get("IE").status, "silver", "evaluated outranks needs-facts");
  assert.equal(u.get("AU").status, "amber", "needs-facts outranks blocked");
  assert.equal(u.get("US-TX").status, "red");
  assert.equal(u.get("US-TX").meta.blocker.kind, BLOCKER_KIND.AWARD_RATE, "Texas-style row states the real award/rate blocker");
});

test("DOMINATED_WITH_PROOF search aggregates create no marker, no blocked card, and stay exactly counted", () => {
  const dom = row("dom", "DOMINATED_WITH_PROOF", ["CA-SK"], { name: "CA-SK + post_vfx_package hybrid search (900 proven dominated)" });
  const a = alloc({
    evaluated: [cand("ev", ["CA-MB"])],
    rows: [dom, row("blk", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", ["CL"])],
    byDisp: { DOMINATED_WITH_PROOF: 308, RULE_REJECTED: 525550, UNPRICEABLE_AUTHORITY_INSUFFICIENT: 1 },
  });
  const p = optimizerProjection(a);
  assert.deepEqual(p.rejected.map((r) => r.structure_id), ["blk"], "no dominated aggregate in blocked cards");
  assert.equal(p.dominatedSearchTotal, 308);
  assert.equal(p.summarizedRuleRejectedTotal, 525550);
  assert.equal(p.rejectedTotal, 1, "blocked total is the true blocked rows, not 525,859");
  const u = buildOptimizerUniverse(a);
  assert.equal(u.has("CA-SK"), false, "a dominated-only jurisdiction gets no red/any marker");
  assert.equal(u.get("CL").status, "red");
});

test("national and subnational jurisdictions stay distinct (CA vs CA-xx, Georgia GE vs US-GA)", () => {
  const a = alloc({
    evaluated: [cand("e1", ["CA-MB"]), cand("e2", ["CA-SK"]), cand("e3", ["US-GA"]), cand("e4", ["GE"])],
    opportunities: [row("copro", "CO_PRO_OPPORTUNITY", ["CA", "FR"])],
  });
  const u = buildOptimizerUniverse(a);
  for (const k of ["CA", "CA-MB", "CA-SK", "US-GA", "GE"]) assert.ok(u.has(k), k);
  assert.equal(u.get("CA").status, "amber", "national co-pro opportunity stays on the national entry");
  assert.equal(u.get("CA-MB").status, "silver");
  assert.equal(u.get("CA-SK").status, "silver");
  assert.equal(globeKey("US-GA"), "US-GA");
  assert.equal(globeKey("GE"), "GE");
  assert.notEqual(u.get("US-GA"), u.get("GE"));
});

test("every marker carries its OWN identity; hover record matches its marker; no blank hover", () => {
  const a = alloc({
    evaluated: [cand("e1", ["CA-MB", "US-GA"]), cand("e2", ["GE", "MN"])],
    opportunities: [row("opp", "CO_PRO_OPPORTUNITY", ["AU"], { reason: "Partner facts required" })],
    rows: [row("blk", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", ["CA-SK"], { rejection_reason_class: "PRICING_BLOCKED", reason: "ceiling award condition cannot be pre-evaluated" })],
  });
  const v = buildGlobeView(a, new Map(), { mode: "optimizer", leadingStructureId: "e1" });
  assert.ok(v.points.length >= 6);
  const seen = new Set();
  for (const p of v.points) {
    assert.ok(!seen.has(p.iso), `one marker per jurisdiction: ${p.iso}`);
    seen.add(p.iso);
    const code = p.jurisdictionCode || p.id;
    assert.equal(p.iso, globeKey(code), "marker iso derives from its own code");
    assert.equal(p.jurisdictionName, JURISDICTION_COORDS[code].name, "name belongs to this exact jurisdiction");
    const h = v.hoverByIso.get(p.iso);
    assert.equal(h.jurisdictionCode, code);
    assert.equal(p.tier, v.categoryByIso.get(p.iso), "marker tier is the jurisdiction's strongest category");
    const hasContent = h.structureLabel || h.blockerReason || h.excludedReason;
    assert.ok(hasContent && p.jurisdictionName, `non-empty hover for ${p.iso}`);
    if (p.tier === "red") assert.ok(h.blockerLabel && h.blockerReason, "blocked marker states its canonical reason");
    if (p.tier === "silver") assert.equal(typeof h.npcUsd, "number");
  }
  assert.equal(v.hoverByIso.get("CA-SK").blockerLabel, "Award / rate confirmation required");
});

test("category sets are disjoint and counts reconcile with the served payload", () => {
  const evaluated = [cand("e1", ["GR", "IT"]), cand("e2", ["GR", "FR"]), cand("e3", ["IT"])];
  const recommended = [cand("r1", ["DE"], { recommendation_status: "RECOMMENDED", is_recommended: true })];
  const a = alloc({ recommended, evaluated, opportunities: [row("o", "CO_PRO_OPPORTUNITY", ["AU"])], rows: [row("b", "RULE_REJECTED", ["CL"])] });
  const p = optimizerProjection(a);
  assert.equal(p.recommended.length + p.evaluated.length, p.executableTotal);
  const ids = [...p.recommended, ...p.evaluated, ...p.opportunities, ...p.rejected].map((s) => s.structure_id);
  assert.equal(new Set(ids).size, ids.length, "every structure appears exactly once across categories");
  const u = buildOptimizerUniverse(a);
  const sum = (k) => [...u.values()].reduce((n, e) => n + e.counts[k], 0);
  assert.equal(sum("evaluated"), evaluated.reduce((n, s) => n + s.participants.length, 0));
  assert.equal(sum("recommended"), 1);
  assert.equal(sum("needsFacts"), 1);
  assert.equal(sum("blocked"), 1);
});

test("selecting another structure changes route/arcs/identity but never the marker universe or categories", () => {
  const a = alloc({ evaluated: [cand("e1", ["GR", "CA-MB"]), cand("e2", ["IT", "CA-SK"]), cand("e3", ["FR"])] });
  const v1 = buildGlobeView(a, new Map(), { mode: "optimizer", leadingStructureId: "e1" });
  const v2 = buildGlobeView(a, new Map(), { mode: "optimizer", leadingStructureId: "e2" });
  assert.notEqual(v1.sceneSignature.structureId, v2.sceneSignature.structureId);
  assert.notDeepEqual(v1.sceneSignature.arcEndpoints, v2.sceneSignature.arcEndpoints);
  assert.deepEqual([...v1.categoryByIso].sort(), [...v2.categoryByIso].sort(), "universe and categories unchanged by selection");
  assert.deepEqual(v1.points.map((p) => p.iso).sort(), v2.points.map((p) => p.iso).sort());
  const mb = v1.points.find((p) => p.iso === "CA-MB");
  assert.equal(mb.selectedRouteUsesJurisdiction, true);
  assert.equal(mb.tier, "silver", "route membership never overwrites the underlying category");
  assert.equal(v1.points.find((p) => p.iso === "FR").selectedRouteUsesJurisdiction, false);
});

test("different projects produce different scenes, lists and hovers from their own payloads", () => {
  const A = alloc({ evaluated: [cand("a1", ["GR", "CA-MB"])], rows: [row("ba", "UNPRICEABLE_AUTHORITY_INSUFFICIENT", ["US-TX"])] });
  const B = alloc({ evaluated: [cand("b1", ["MU", "GB"]), cand("b2", ["IE"])], opportunities: [row("ob", "CO_PRO_OPPORTUNITY", ["AU"])] });
  const va = buildGlobeView(A, new Map(), { mode: "optimizer" });
  const vb = buildGlobeView(B, new Map(), { mode: "optimizer" });
  assert.notDeepEqual(va.sceneSignature.markerCodes, vb.sceneSignature.markerCodes);
  assert.notEqual(va.sceneSignature.structureId, vb.sceneSignature.structureId);
  assert.ok(va.hoverByIso.has("US-TX") && !vb.hoverByIso.has("US-TX"));
});

test("blocker taxonomy keeps the canonical dispositions distinct", () => {
  const k = (r) => classifyBlocker(r).kind;
  assert.equal(k({ candidate_status: "UNPRICEABLE_AUTHORITY_INSUFFICIENT", rejection_reason_class: "PRICING_BLOCKED", reason: "rate CEILING award condition(s) cannot be pre-evaluated" }), BLOCKER_KIND.AWARD_RATE);
  assert.equal(k({ candidate_status: "UNPRICEABLE_AUTHORITY_INSUFFICIENT", rejection_reason_class: "UNPRICEABLE_AUTHORITY_INSUFFICIENT" }), BLOCKER_KIND.AUTHORITY);
  assert.equal(k({ candidate_status: "UNPRICEABLE_AUTHORITY_INSUFFICIENT", rejection_reason_class: "PRICING_BLOCKED", reason: "statutory rate did not resolve ... minimum-spend or eligibility conditions unmet" }), BLOCKER_KIND.ELIGIBILITY);
  assert.equal(k({ candidate_status: "FEASIBILITY_REVIEW_REQUIRED", rejection_reason_class: "NON_GUARANTEED_SELECTIVE" }), BLOCKER_KIND.SELECTIVE);
  assert.equal(k({ candidate_status: "FEASIBILITY_REVIEW_REQUIRED", rejection_reason_class: "SUPERSEDED" }), BLOCKER_KIND.SUPERSEDED);
  assert.equal(k({ candidate_status: "FEASIBILITY_REVIEW_REQUIRED", rejection_reason_class: "AUTHORITY_UNRESOLVED_NON_PRICEABLE", reason: "the production's statutory conditions are unmet" }), BLOCKER_KIND.ELIGIBILITY);
  assert.equal(k({ candidate_status: "RULE_REJECTED", rejection_reason_class: "PAIRWISE_INCOMPATIBLE" }), BLOCKER_KIND.PROHIBITED);
  assert.equal(k({ candidate_status: "DOMINATED_WITH_PROOF" }), BLOCKER_KIND.DOMINATED);
});

test("Globe3D recreates index-keyed hit targets and beacons from the CURRENT datum when markers change", () => {
  const src = readSrc("components/Globe3D.jsx");
  assert.match(src, /globe\.htmlElement\(\(d\) => baseHtml\(d\)\)/);
  assert.match(src, /globe\.customThreeObject\(\(d\) => baseBeacon\(d\)\)/);
  assert.match(src, /el\.dataset\.iso = d\.iso/);
  const card = readSrc("components/GlobeHoverCard.jsx");
  assert.match(card, /hover\.jurisdictionName \|\| hover\.name/);
  assert.match(card, /Structures represented/);
});

test("Globe3D hit targets: back-face hiding is wired, hit-boxes are uniform and never intercept a neighbour, hover/click resolve to the nearest marker", () => {
  const src = readSrc("components/Globe3D.jsx");
  // three-globe only hides far-side html targets after setPointOfView(camera); it was never called
  assert.match(src, /povGlobe\.setPointOfView\(camera\)/);
  // CSS2DRenderer rewrites `display` every pass, so visibility/pointer-events carry the hiding
  assert.match(src, /el\.style\.visibility = isVisible \? "" : "hidden"/);
  assert.match(src, /el\.style\.pointerEvents = isVisible \? "auto" : "none"/);
  // one hit-box size, one z-index: a route marker must not cover its neighbours
  assert.match(src, /const size = 24;/);
  assert.doesNotMatch(src, /isExactRoute \? 40 : 28/);
  assert.doesNotMatch(src, /isExactRoute \? "46" : "45"/);
  // nearest-centre resolution for overlapping boxes (hover and click)
  assert.match(src, /document\.elementsFromPoint/);
  assert.match(src, /el\.__globeDatum = d/);
  const card = readSrc("components/GlobeHoverCard.jsx");
  assert.match(card, /pointerEvents: "none"/, "the hover card must never intercept the next pointer target");
});

test("Optimizer Globe marker click resolves its own jurisdiction in every mounting screen", () => {
  const globe = readSrc("screens/production/ProjectGlobe.jsx");
  assert.match(globe, /setSelectedJurisdiction\(pt\.jurisdictionCode \|\| pt\.id\)/);
  assert.match(globe, /Summarized search space \(not individual structures\)/);
  const ws = readSrc("screens/production/Workspace.jsx");
  assert.match(ws, /optimizer-rejection", buildRejectedDetail\(s\)/);
  assert.match(ws, /optimizer-opportunity", buildOpportunityDetail\(s\)/);
});

