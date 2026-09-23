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

test("producer optimizer keeps the six-card contract: leading slots fill from RECOMMENDED only, never padded with evaluated alternatives", () => {
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
  // Only 3 real recommended options exist -- an honest, shorter rack (anchor + 3),
  // never backfilled with the evaluated alternative to reach 6.
  assert.deepEqual(result.slots.map((s) => s.structure_id), ["anchor", "rec-1", "rec-2", "rec-3"]);
  assert.equal(result.slot6, null);
  assert.deepEqual(result.dropdownOptions, []);
  assert.deepEqual(result.dropdownEvaluatedAlternatives.map((s) => s.structure_id), ["alt-cheap"], (
    "the evaluated alternative remains reachable via the dropdown's own labeled section, never silently dropped"
  ));
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
  // The exact regression this rewrite fixes: Advanced Multi-Jurisdiction must
  // be back as a real Full Globe section, never removed.
  assert.match(globeSource, /ADVANCED_MULTI_JURISDICTION/);
  assert.match(globeSource, /Advanced Multi-Jurisdiction/);
});
