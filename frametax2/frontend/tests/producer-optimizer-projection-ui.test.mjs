import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { MODE_OPTIMIZER, admissibleForMode, selectSixSlots } from "../src/lib/workspaceScenarioMode.js";
import { selectMaxPotentialCard } from "../src/lib/productionOptions.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (path) => readFileSync(join(SRC, path), "utf8");
const stripComments = (source) => source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

function candidate(id, npc = 700_000) {
  return {
    structure_id: id,
    economic_identity: `econ-${id}`,
    classification: "HYBRID_ANCHOR_COMPONENT",
    primary_jurisdiction: "GR",
    participants: ["GR", "CA-MB"],
    npc_with_adjustments_usd: npc,
    is_fully_priced: true,
  };
}

test("producer UI reads only producer_optimizer_options while exhaustive optimizer arrays remain available", () => {
  const producer = candidate("producer");
  const exhaustive = candidate("three-country", 500_000);
  exhaustive.participants = ["GR", "CA-MB", "IT"];
  const allocated = {
    structures: [],
    best_per_jurisdiction: {},
    optimizer_candidates: [producer, exhaustive],
    optimizer_scenarios: [producer, exhaustive],
    producer_optimizer_options: [producer],
  };
  assert.deepEqual(admissibleForMode(allocated, MODE_OPTIMIZER), [producer]);
  assert.equal(allocated.optimizer_scenarios.length, 2, "exhaustive audit projection remains unchanged");
  assert.equal(selectMaxPotentialCard(allocated, new Set()).structure, producer);
});

test("producer optimizer keeps the six-card and complete dropdown contract", () => {
  const anchor = { ...candidate("anchor", 1_000_000), is_baseline: true, structure_type: "single_country" };
  const options = Array.from({ length: 8 }, (_, i) => candidate(`option-${i + 1}`, 600_000 + i));
  const allocated = { structures: [anchor], best_per_jurisdiction: {}, producer_optimizer_options: options };
  const result = selectSixSlots(allocated, MODE_OPTIMIZER, null);
  assert.deepEqual(result.slots.map((s) => s.structure_id), [
    "anchor", "option-1", "option-2", "option-3", "option-4", "option-5",
  ]);
  assert.deepEqual(result.dropdownOptions.map((s) => s.structure_id), [
    "option-5", "option-6", "option-7", "option-8",
  ]);
});

test("Workspace, Overview, and Full Globe are wired to the canonical producer collections", () => {
  const modeSource = stripComments(read("lib/workspaceScenarioMode.js"));
  const optionSource = stripComments(read("lib/productionOptions.js"));
  const workspaceSource = stripComments(read("screens/production/Workspace.jsx"));
  const overviewSource = stripComments(read("screens/production/Overview.jsx"));
  const globeSource = stripComments(read("screens/production/ProjectGlobe.jsx"));
  assert.match(modeSource, /producer_optimizer_options/);
  assert.match(optionSource, /producer_optimizer_options/);
  assert.match(workspaceSource, /selectSixSlots/);
  assert.match(overviewSource, /IncentiveIntelligence/);
  assert.match(globeSource, /admissibleForMode/);
  assert.doesNotMatch(globeSource, /ADVANCED_MULTI_JURISDICTION/);
  assert.match(workspaceSource, /each saves more than \$100K/);
});
