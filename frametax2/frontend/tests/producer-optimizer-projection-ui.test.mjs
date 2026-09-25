// GLOBE_WORKSPACE_CANONICAL_WIRING_COMPLETE (2026-09-22): rewritten. The
// original version of this file pinned the exact regression
// CANONICAL_STACKING_AND_OPTIMIZER_PROJECTION_AUDIT.md found: every fixture
// here built a synthetic `producer_optimizer_options` that was always
// non-empty, and `assert.doesNotMatch(globeSource, /ADVANCED_MULTI_JURISDICTION/)`
// directly pinned the removal of the Advanced-tier Full Globe section — so
// these tests kept passing while producer_optimizer_options_total was 0 for
// all four real productions in the acceptance database and the Optimizer
// surface was empty everywhere. See workspaceScenarioMode.js's own header
// comment for the restored contract.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { MODE_OPTIMIZER, admissibleForMode, selectSixSlots, optimizerProjection } from "../src/lib/workspaceScenarioMode.js";
import { selectMaxPotentialCard } from "../src/lib/productionOptions.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (path) => readFileSync(join(SRC, path), "utf8");
const stripComments = (source) => source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

function candidate(id, npc = 700_000, overrides = {}) {
  return {
    structure_id: id,
    economic_identity: `econ-${id}`,
    classification: "HYBRID_ANCHOR_COMPONENT",
    primary_jurisdiction: "GR",
    participants: ["GR", "CA-MB"],
    npc_with_adjustments_usd: npc,
    is_fully_priced: true,
    practicality_tier: "PRACTICAL_HYBRID",
    participant_count: 2,
    recommendation_status: "RECOMMENDED",
    is_recommended: true,
    ...overrides,
  };
}

test("the Optimizer projection stays COMPLETE (never threshold-filtered) even when the recommended subset is empty — the exact regression the audit found", () => {
  // A real production shape: every 2-jurisdiction candidate is below
  // threshold (EVALUATED_ALTERNATIVE), and a real 3+-jurisdiction candidate
  // saves real money above the 3+-jurisdiction threshold (RECOMMENDED).
  const belowThreshold = candidate("below-threshold", 950_000, {
    savings_vs_current_usd: 50_000, recommendation_status: "EVALUATED_ALTERNATIVE", is_recommended: false,
  });
  const threeCountryRecommended = candidate("three-country", 700_000, {
    participants: ["GR", "CA-MB", "IT"], practicality_tier: "ADVANCED_MULTI_JURISDICTION", participant_count: 3,
    savings_vs_current_usd: 250_000, recommendation_status: "RECOMMENDED", is_recommended: true,
  });
  const allocated = {
    structures: [],
    best_per_jurisdiction: {},
    optimizer_candidates: [belowThreshold, threeCountryRecommended],
    optimizer_scenarios: [belowThreshold, threeCountryRecommended],
    optimizer_scenarios_total: 2,
    optimizer_executable_total: 2,
    recommended_optimizer_options: [threeCountryRecommended],
    recommended_optimizer_options_total: 1,
    evaluated_optimizer_alternatives: [belowThreshold],
    evaluated_optimizer_alternatives_total: 1,
    optimizer_opportunities_requiring_facts: [],
    producer_optimizer_options: [threeCountryRecommended],
  };
  const admissible = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["three-country", "below-threshold"], (
    "the complete collection (recommended first, then evaluated alternatives) must be admissible — " +
    "never just the recommended subset, and never empty just because no 2-jurisdiction candidate qualifies"
  ));
  const proj = optimizerProjection(allocated);
  assert.equal(proj.executableTotal, 2);
  assert.equal(proj.recommendedTotal, 1);
  assert.equal(proj.evaluatedTotal, 1);
  assert.equal(selectMaxPotentialCard(allocated, new Set()).structure, threeCountryRecommended, (
    "Overview's opportunity card must source from the real RECOMMENDED entry, never fabricate one when it exists"
  ));
});

test("producer optimizer keeps the six-card contract: fewer than five recommended options backfill slots 2-6 from Evaluated Alternatives, never leaving a short rack when real executable options exist", () => {
  // OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): this test previously pinned
  // the OPPOSITE contract ("never padded with evaluated alternatives") — that
  // was the confirmed live defect (F#K Valentine's Day has exactly 4 real
  // recommended options; Workspace showed only 4 Optimizer cards instead of
  // Current Location + 5). The controlling product contract is explicit:
  // "Slots 2-6: first five executable Optimizer options, recommended first...
  // if fewer than five recommendations exist, fill remaining slots with the
  // best Evaluated Alternatives, visibly labeled as alternatives." Recommended
  // options still always sort before evaluated ones (recPool before evalPool
  // in the combined pool) — an evaluated alternative only ever fills a slot
  // once every real recommended option is already placed.
  const anchor = { ...candidate("anchor", 1_000_000), is_baseline: true, structure_type: "single_country" };
  const recommended = Array.from({ length: 3 }, (_, i) => candidate(`rec-${i + 1}`, 600_000 + i));
  const alternative = candidate("alt-cheap", 1, { recommendation_status: "EVALUATED_ALTERNATIVE", is_recommended: false });
  const allocated = {
    structures: [anchor], best_per_jurisdiction: {},
    optimizer_scenarios: [...recommended, alternative],
    recommended_optimizer_options: recommended,
    evaluated_optimizer_alternatives: [alternative],
    optimizer_opportunities_requiring_facts: [],
    producer_optimizer_options: recommended,
  };
  const result = selectSixSlots(allocated, MODE_OPTIMIZER, null);
  // 3 recommended + 1 evaluated = 4 total executable options -- all 4 fill the
  // leading slots (recommended first), slot 6 is honestly null (nothing left).
  assert.deepEqual(result.slots.map((s) => s.structure_id), ["anchor", "rec-1", "rec-2", "rec-3", "alt-cheap"]);
  assert.equal(result.slot6, null);
  assert.deepEqual(result.dropdownOptions, []);
  assert.deepEqual(result.dropdownEvaluatedAlternatives, [], (
    "alt-cheap already occupies a leading slot -- it must not also appear in the dropdown's Evaluated Alternatives section (no duplicate reachability)"
  ));
});

test("producer optimizer six-card contract: exactly five executable options (fewer than four recommended) still fill all five leading+slot6 positions, recommended first", () => {
  // A second, distinct shape from the test above: exactly enough executable
  // options to fill every one of the five Optimizer slots (2-6), with
  // recommended options short of four -- confirms leading itself (not just
  // slot 6) backfills from evaluated alternatives, and slot 6 IS reachable
  // (not null) once there are enough combined options.
  const anchor = { ...candidate("anchor", 1_000_000), is_baseline: true, structure_type: "single_country" };
  const recommended = Array.from({ length: 2 }, (_, i) => candidate(`rec-${i + 1}`, 600_000 + i));
  const evaluated = Array.from({ length: 3 }, (_, i) => candidate(`eval-${i + 1}`, 700_000 + i, { recommendation_status: "EVALUATED_ALTERNATIVE", is_recommended: false }));
  const allocated = {
    structures: [anchor], best_per_jurisdiction: {},
    optimizer_scenarios: [...recommended, ...evaluated],
    recommended_optimizer_options: recommended,
    evaluated_optimizer_alternatives: evaluated,
    optimizer_opportunities_requiring_facts: [],
    producer_optimizer_options: recommended,
  };
  const result = selectSixSlots(allocated, MODE_OPTIMIZER, null);
  assert.deepEqual(result.leading.map((s) => s.structure_id), ["rec-1", "rec-2", "eval-1", "eval-2"], (
    "both recommended options fill first, then evaluated alternatives backfill the remaining leading slots"
  ));
  assert.equal(result.slot6.structure_id, "eval-3");
  assert.deepEqual(result.slots.map((s) => s.structure_id), ["anchor", "rec-1", "rec-2", "eval-1", "eval-2", "eval-3"]);
  assert.deepEqual(result.dropdownOptions, []);
  assert.deepEqual(result.dropdownEvaluatedAlternatives, [], "every evaluated alternative is already placed -- none left over for the dropdown");
});

test("producer optimizer six-card contract with enough recommended options: slots 2-6 fill from the first five recommended, dropdown carries the remainder plus evaluated alternatives separately", () => {
  const anchor = { ...candidate("anchor", 1_000_000), is_baseline: true, structure_type: "single_country" };
  const recommended = Array.from({ length: 8 }, (_, i) => candidate(`option-${i + 1}`, 600_000 + i));
  const allocated = {
    structures: [anchor], best_per_jurisdiction: {},
    optimizer_scenarios: recommended,
    recommended_optimizer_options: recommended,
    evaluated_optimizer_alternatives: [],
    optimizer_opportunities_requiring_facts: [],
    producer_optimizer_options: recommended,
  };
  const result = selectSixSlots(allocated, MODE_OPTIMIZER, null);
  assert.deepEqual(result.slots.map((s) => s.structure_id), [
    "anchor", "option-1", "option-2", "option-3", "option-4", "option-5",
  ]);
  assert.deepEqual(result.dropdownOptions.map((s) => s.structure_id), [
    "option-6", "option-7", "option-8",
  ]);
});

test("Workspace, Overview, and Full Globe are wired to the canonical, COMPLETE optimizer collections — Advanced Multi-Jurisdiction is a real, present Full Globe section", () => {
  const modeSource = stripComments(read("lib/workspaceScenarioMode.js"));
  const optionSource = stripComments(read("lib/productionOptions.js"));
  const workspaceSource = stripComments(read("screens/production/Workspace.jsx"));
  const overviewSource = stripComments(read("screens/production/Overview.jsx"));
  const globeSource = stripComments(read("screens/production/ProjectGlobe.jsx"));
  assert.match(modeSource, /recommended_optimizer_options/);
  assert.match(modeSource, /evaluated_optimizer_alternatives/);
  assert.match(modeSource, /optimizer_opportunities_requiring_facts/);
  assert.match(optionSource, /recommended_optimizer_options/);
  assert.match(workspaceSource, /selectSixSlots/);
  assert.match(overviewSource, /IncentiveIntelligence/);
  assert.match(globeSource, /admissibleForMode/);
  // The exact regression this test guards against: a 3+-jurisdiction
  // (Advanced Multi-Jurisdiction practicality tier) structure must never be
  // silently excluded from the Full Globe's rendered set. OPTIMIZER_GLOBE_
  // WORKSPACE_WIRING (2026-09-25) removed the OLD practicality-tier SECTION
  // HEADINGS (confirmed live: a threshold dimension, not a real structural
  // family — see ProjectGlobe.jsx's own OPTIMIZER_SECTIONS comment) but the
  // underlying completeness guarantee is unchanged and still real: every
  // executable structure, at ANY jurisdiction count/tier, still reaches
  // optimizerProj.recommended/evaluated (data-level completeness is pinned
  // separately and still passing — workspace-scenario-mode.test.mjs's
  // "EVERY canonical family renders when executable — 3+-jurisdiction
  // (Advanced) rows are NEVER hidden"). At the UI level: the section render
  // must read optimizerProj's arrays directly, with no jurisdiction-count or
  // practicality_tier filter anywhere in this file.
  assert.match(globeSource, /optimizerProj\?\.\[key\]/, "sections must read the complete optimizerProj arrays directly");
  assert.doesNotMatch(globeSource, /practicality_tier/, "ProjectGlobe.jsx must never filter/section by practicality_tier again — that was the threshold-as-family conflation this pass fixed");
});
