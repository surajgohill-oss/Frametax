// ── GW-OI-002/003/004/005 — Optimizer category coverage, family/tier
// separation, route-detail, and tie/equivalence presentation ─────────────
//
// Run with: npm test (node --test)
//
// Pure logic tests — no JSX, no backend, no live economics. Every input is
// a hand-built structure/allocated payload shaped like the real
// canonical_production_view.py served response. Generic across any
// jurisdiction/family/tier combination — no assertion here depends on a
// specific project ID, project name, or jurisdiction code by name.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  buildOptimizerCategorySummary, buildSingleJurisdictionCategorySummary,
  classifyRouteTies, OPTIMIZER_FAMILIES, PRACTICALITY_TIERS,
} from "../src/lib/productionOptions.js";
import { OPTIMIZER_FAMILY_LABEL, PRACTICALITY_TIER_LABEL } from "../src/lib/globeData.js";
import { buildScenarioLabel, buildRouteOptionDetail } from "../src/lib/scenarioLabel.js";

const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

function structure(overrides) {
  return {
    structure_id: "s1",
    economic_identity: "econ-s1",
    classification: "HYBRID_ANCHOR_COMPONENT",
    practicality_tier: "PRACTICAL_HYBRID",
    primary_jurisdiction: "US",
    participants: ["US"],
    participant_count: 1,
    is_fully_priced: true,
    recommendation_status: "RECOMMENDED",
    candidate_status: "PRICED",
    npc_with_adjustments_usd: 1_000_000,
    selected_incentive_usd: 200_000,
    segments: [],
    component_allocations: [],
    ...overrides,
  };
}

// ── 1/2/6. Overview category-complete summary, honest empty states ───────

test("buildOptimizerCategorySummary: exposes every canonical family, including honest zero-executable states — never fabricates a candidate", () => {
  const allocated = {
    optimizer_scenarios_by_family: { HYBRID_ANCHOR_COMPONENT: 171, OFFICIAL_COPRODUCTION: 0, COMBINED_COPRO_HYBRID_STACK: 0, MULTI_PRINCIPAL_MULTILATERAL: 0 },
    optimizer_scenarios_by_tier: { PRACTICAL_HYBRID: 93, FORMAL_COPRODUCTION: 0, ADVANCED_MULTI_JURISDICTION: 78 },
    top_by_structural_family: { HYBRID_ANCHOR_COMPONENT: [structure({ structure_id: "rep-1" })], OFFICIAL_COPRODUCTION: [], COMBINED_COPRO_HYBRID_STACK: [], MULTI_PRINCIPAL_MULTILATERAL: [] },
    optimizer_executable_total: 171,
    recommended_optimizer_options_total: 66,
    evaluated_optimizer_alternatives_total: 105,
    optimizer_opportunities_requiring_facts_total: 25,
  };
  const summary = buildOptimizerCategorySummary(allocated);
  assert.equal(summary.families.length, OPTIMIZER_FAMILIES.length, "every canonical family must be present, populated or not");
  const byKey = Object.fromEntries(summary.families.map((f) => [f.key, f]));
  assert.equal(byKey.HYBRID_ANCHOR_COMPONENT.executableCount, 171);
  assert.equal(byKey.HYBRID_ANCHOR_COMPONENT.representative.structure_id, "rep-1");
  // The other three families are honestly zero — never a fabricated representative.
  for (const key of ["OFFICIAL_COPRODUCTION", "COMBINED_COPRO_HYBRID_STACK", "MULTI_PRINCIPAL_MULTILATERAL"]) {
    assert.equal(byKey[key].executableCount, 0, `${key} must show its real zero count`);
    assert.equal(byKey[key].representative, null, `${key} must never fabricate a representative when it has none`);
  }
  assert.equal(summary.tiers.length, PRACTICALITY_TIERS.length);
  const tierByKey = Object.fromEntries(summary.tiers.map((t) => [t.key, t]));
  assert.equal(tierByKey.PRACTICAL_HYBRID.executableCount, 93);
  assert.equal(tierByKey.FORMAL_COPRODUCTION.executableCount, 0);
  assert.equal(tierByKey.ADVANCED_MULTI_JURISDICTION.executableCount, 78);
  assert.equal(summary.recommendedTotal, 66);
  assert.equal(summary.evaluatedTotal, 105);
  assert.equal(summary.needsMoreFactsTotal, 25);
  assert.equal(summary.executableTotal, 171);
});

test("buildOptimizerCategorySummary: a production with genuinely zero optimizer scenarios still returns an honest all-zero summary, never null/undefined counts", () => {
  const allocated = {
    optimizer_scenarios_by_family: {}, optimizer_scenarios_by_tier: {}, top_by_structural_family: {},
    optimizer_executable_total: 0, recommended_optimizer_options_total: 0, evaluated_optimizer_alternatives_total: 0, optimizer_opportunities_requiring_facts_total: 0,
  };
  const summary = buildOptimizerCategorySummary(allocated);
  for (const f of summary.families) { assert.equal(f.executableCount, 0); assert.equal(f.representative, null); }
  for (const t of summary.tiers) assert.equal(t.executableCount, 0);
  assert.equal(summary.executableTotal, 0);
});

test("buildSingleJurisdictionCategorySummary: winner count and unique-jurisdiction count from best_per_jurisdiction, generic across any code set", () => {
  const allocated = {
    best_per_jurisdiction: {
      AA: structure({ structure_id: "a", primary_jurisdiction: "AA" }),
      BB: structure({ structure_id: "b", primary_jurisdiction: "BB" }),
      CC: null, // a real served null must never be counted as a winner
    },
    top_by_structural_family: { STACKED_PROGRAMS: [structure({ structure_id: "stack1" }), structure({ structure_id: "stack2" })] },
  };
  const summary = buildSingleJurisdictionCategorySummary(allocated);
  assert.equal(summary.winnerCount, 2);
  assert.equal(summary.uniqueJurisdictionCount, 2);
  assert.equal(summary.stackedProgramCount, 2);
});

// ── 2. Overview mode changes update the summary (behavioral, not just
// existence) — different `allocated` inputs produce different summaries,
// proving the function is genuinely mode/data-driven. ────────────────────
test("category summaries are genuinely data-driven: different allocated payloads produce different summaries", () => {
  const empty = buildOptimizerCategorySummary({ optimizer_scenarios_by_family: {}, optimizer_scenarios_by_tier: {}, top_by_structural_family: {}, optimizer_executable_total: 0, recommended_optimizer_options_total: 0, evaluated_optimizer_alternatives_total: 0, optimizer_opportunities_requiring_facts_total: 0 });
  const populated = buildOptimizerCategorySummary({ optimizer_scenarios_by_family: { HYBRID_ANCHOR_COMPONENT: 5 }, optimizer_scenarios_by_tier: { PRACTICAL_HYBRID: 5 }, top_by_structural_family: { HYBRID_ANCHOR_COMPONENT: [structure()] }, optimizer_executable_total: 5, recommended_optimizer_options_total: 2, evaluated_optimizer_alternatives_total: 3, optimizer_opportunities_requiring_facts_total: 0 });
  assert.notEqual(empty.executableTotal, populated.executableTotal);
});

// ── 3/4. Family and tier are independent axes — an Advanced scenario never
// displays "Practical Hybrid". ────────────────────────────────────────────

test("OPTIMIZER_FAMILY_LABEL never contains the word 'Practical' — family and tier must never be conflated by label text", () => {
  for (const key of OPTIMIZER_FAMILIES) {
    assert.ok(!/practical/i.test(OPTIMIZER_FAMILY_LABEL[key]), `${key}'s family label ("${OPTIMIZER_FAMILY_LABEL[key]}") must not claim a practicality tier`);
  }
});

test("PRACTICALITY_TIER_LABEL and OPTIMIZER_FAMILY_LABEL are two independent maps — an Advanced-tier HYBRID_ANCHOR_COMPONENT scenario resolves a family label with no tier claim and a distinct, correct tier label", () => {
  const advanced = structure({ classification: "HYBRID_ANCHOR_COMPONENT", practicality_tier: "ADVANCED_MULTI_JURISDICTION" });
  const familyLabel = OPTIMIZER_FAMILY_LABEL[advanced.classification];
  const tierLabel = PRACTICALITY_TIER_LABEL[advanced.practicality_tier];
  assert.equal(familyLabel, "Hybrid Anchor + Component");
  assert.equal(tierLabel, "Advanced Multi-Jurisdiction");
  assert.notEqual(`${familyLabel} · ${tierLabel}`, "Practical Hybrid", "the combined label must never collapse to the old, incorrect single string");
  assert.ok(!/practical/i.test(familyLabel));
});

test("every canonical family has a real, distinct label, and every canonical tier has a real, distinct label — no two collide", () => {
  const familyLabels = OPTIMIZER_FAMILIES.map((k) => OPTIMIZER_FAMILY_LABEL[k]);
  const tierLabels = PRACTICALITY_TIERS.map((k) => PRACTICALITY_TIER_LABEL[k]);
  assert.equal(new Set(familyLabels).size, familyLabels.length, "family labels must all be distinct");
  assert.equal(new Set(tierLabels).size, tierLabels.length, "tier labels must all be distinct");
  for (const fl of familyLabels) assert.ok(!tierLabels.includes(fl), "no family label may equal a tier label verbatim");
});

// ── 10/11/12. Multi-party route component-allocation disclosure ─────────

test("buildRouteOptionDetail: appends real allocated amounts per routed leg, generic across any jurisdiction/program", () => {
  const s = structure({
    primary_jurisdiction: "ZZ",
    participants: ["ZZ", "YY", "XX"],
    participant_count: 3,
    practicality_tier: "ADVANCED_MULTI_JURISDICTION",
    component_allocations: [
      { jurisdiction_code: "ZZ", component: "principal_production", allocated_usd: 4_302_827 },
      { jurisdiction_code: "YY", component: "post", allocated_usd: 9_068 },
      { jurisdiction_code: "XX", component: "vfx", allocated_usd: 52_500 },
    ],
  });
  const detail = buildRouteOptionDetail(s);
  assert.match(detail, /\$4\.3M/, "principal production amount must appear, compact-formatted");
  assert.match(detail, /\$9K/, "the smaller routed leg's amount must appear");
  assert.match(detail, /\$53K/, "the third leg's amount must appear, compact-rounded like CompactMoney");
  // Must still contain the real route (jurisdiction/component) text from buildScenarioLabel.
  assert.equal(detail.startsWith(buildScenarioLabel(s)), true, "must extend, never replace, the canonical route label");
});

test("buildRouteOptionDetail: falls back to the plain scenario label when no component_allocations exist — never fabricates an amount", () => {
  const s = structure({ component_allocations: [] });
  assert.equal(buildRouteOptionDetail(s), buildScenarioLabel(s));
});

// ── 5/7/8/9/10/11/12/13. Tie and equivalent-route-variant classification ─

test("classifyRouteTies: structures with distinct NPCs are never grouped as a tie", () => {
  const groups = classifyRouteTies([structure({ structure_id: "a", npc_with_adjustments_usd: 100 }), structure({ structure_id: "b", npc_with_adjustments_usd: 200 })]);
  assert.equal(groups.length, 0);
});

test("classifyRouteTies: EQUIVALENT ROUTE VARIANTS — different economic identities/routes, identical full economic signature, preserved (never deleted) and grouped with a stable representative", () => {
  const a = structure({ structure_id: "a", economic_identity: "econ-b", primary_jurisdiction: "AA", npc_with_adjustments_usd: 500_000, selected_incentive_usd: 100_000, recommendation_status: "EVALUATED_ALTERNATIVE" });
  const b = structure({ structure_id: "b", economic_identity: "econ-a", primary_jurisdiction: "BB", npc_with_adjustments_usd: 500_000, selected_incentive_usd: 100_000, recommendation_status: "EVALUATED_ALTERNATIVE" });
  const groups = classifyRouteTies([a, b]);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].type, "EQUIVALENT_ROUTE_VARIANTS");
  assert.equal(groups[0].members.length, 2, "both real routes must be preserved, never one deleted");
  // Stable, deterministic representative — economic_identity order, never structure_id/enumeration order.
  assert.equal(groups[0].representative.economic_identity, "econ-a");
});

test("classifyRouteTies: NPC-ONLY TIE — same NPC but materially different QPE/incentive/status stays separate and is never collapsed", () => {
  const a = structure({ structure_id: "a", economic_identity: "econ-a", npc_with_adjustments_usd: 500_000, selected_incentive_usd: 100_000, recommendation_status: "RECOMMENDED" });
  const b = structure({ structure_id: "b", economic_identity: "econ-b", npc_with_adjustments_usd: 500_000, selected_incentive_usd: 250_000, recommendation_status: "EVALUATED_ALTERNATIVE" });
  const groups = classifyRouteTies([a, b]);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].type, "NPC_ONLY_TIE");
  assert.equal(groups[0].variants.length, 2, "two materially different economic outcomes must remain visibly distinct");
  assert.equal(groups[0].members.length, 2, "no member may be dropped");
});

test("classifyRouteTies: does not use structure_id or array/enumeration order as the tie-break — economic_identity decides the stable representative", () => {
  const late = structure({ structure_id: "zzz-should-not-win", economic_identity: "aaa-econ", npc_with_adjustments_usd: 500_000, selected_incentive_usd: 100_000 });
  const early = structure({ structure_id: "aaa-should-not-matter", economic_identity: "zzz-econ", npc_with_adjustments_usd: 500_000, selected_incentive_usd: 100_000 });
  // `late` is passed AFTER `early` in array order but has the alphabetically-first economic_identity.
  const groups = classifyRouteTies([early, late]);
  assert.equal(groups[0].representative.economic_identity, "aaa-econ", "the alphabetically-first economic_identity must win regardless of array position or structure_id");
});

test("classifyRouteTies: a genuine three-way NPC tie preserves all three real routes, none deleted", () => {
  const s1 = structure({ structure_id: "1", economic_identity: "e1", npc_with_adjustments_usd: 500_000, selected_incentive_usd: 100_000, recommendation_status: "RECOMMENDED" });
  const s2 = structure({ structure_id: "2", economic_identity: "e2", npc_with_adjustments_usd: 500_000, selected_incentive_usd: 100_000, recommendation_status: "RECOMMENDED" }); // equivalent to s1
  const s3 = structure({ structure_id: "3", economic_identity: "e3", npc_with_adjustments_usd: 500_000, selected_incentive_usd: 300_000, recommendation_status: "EVALUATED_ALTERNATIVE" }); // NPC tie only
  const groups = classifyRouteTies([s1, s2, s3]);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].type, "NPC_ONLY_TIE");
  const totalPreserved = groups[0].variants.reduce((sum, v) => sum + v.members.length, 0);
  assert.equal(totalPreserved, 3, "all three real structures must be reachable — s1/s2 grouped as equivalent within the tie, s3 kept as its own distinct variant");
});

// ── 14. Generic — no project-specific IDs or jurisdiction-specific
// patches anywhere in the new presentation logic. ────────────────────────
test("new presentation logic's CODE (not its explanatory comments) contains no hardcoded project ID, project name, or jurisdiction-specific branch", () => {
  const src = stripComments(readFileSync(new URL("../src/lib/productionOptions.js", import.meta.url), "utf8"));
  assert.ok(!/Mauritius|Little Utopia|Lips Like Sugar|Bad Hombres|Valentine/i.test(src));
});
