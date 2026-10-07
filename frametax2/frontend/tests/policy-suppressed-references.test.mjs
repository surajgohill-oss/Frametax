import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { policySuppressedLabel, policySuppressedRows } from "../src/lib/jurisdictionUniverse.js";

const allocated = {
  music_carveout: { threshold_usd: 25000 },
  optimizer_scenarios: [{ structure_id: "curated-1", label: "never read here" }],
  optimizer_scenarios_music_suppressed: [
    {
      structure_id: "s1", label: "CA-MB + music_package->BE", npc_with_adjustments_usd: 1630334.55,
      component_allocations: [{ component: "principal_production", jurisdiction_code: "CA-MB" }, { component: "music_package", jurisdiction_code: "BE" }],
      music_carveout_status: "SUPPRESSED_BELOW_THRESHOLD", music_carveout_delta_usd: -222750, music_carveout_threshold_usd: 25000,
      music_carveout_reason: "below the $25,000 carve-out threshold",
      music_carveout_counterpart: { kind: "BUNDLED_REPRICED_COUNTERFACTUAL", host_component: "principal_production", host_jurisdiction_code: "CA-MB",
        music_jurisdiction_code: "BE", bundled_npc_with_adjustments_usd: 1407584.55 },
    },
    {
      structure_id: "s2", label: "US-CA anchor — music_package routed to BG", npc_with_adjustments_usd: 8545052.5,
      component_allocations: [{ component: "music_package", jurisdiction_code: "BG" }],
      music_carveout_status: "SUPPRESSED_COUNTERPART_NOT_ESTABLISHED", music_carveout_delta_usd: null, music_carveout_reason: "not established",
      music_carveout_counterpart: null,
    },
  ],
};

test("every served policy-suppressed structure becomes one reference row with the required fields", () => {
  const rows = policySuppressedRows(allocated);
  assert.deepEqual(rows.map((r) => r.id), ["s1", "s2"]);
  const [a, b] = rows;
  assert.equal(a.route, "CA-MB + music_package->BE");
  assert.ok(a.musicDestination);
  assert.match(a.bundledRoute, /^Music bundled with principal production in /);
  assert.equal(a.bundledNpc, 1407584.55);
  assert.equal(a.delta, -222750);
  assert.equal(a.threshold, 25000);
  assert.equal(a.reason, "below the $25,000 carve-out threshold");
  assert.equal(b.bundledRoute, "Not established");
  assert.equal(b.delta, null);
  assert.equal(b.threshold, 25000, "falls back to the served policy threshold");
  assert.equal(b.structure, allocated.optimizer_scenarios_music_suppressed[1], "opens the served entry itself");
});

test("the surface reads only the suppressed list and is absent when there is nothing to show", () => {
  assert.deepEqual(policySuppressedRows({ optimizer_scenarios: [{ structure_id: "x" }] }), []);
  assert.equal(policySuppressedLabel(1), "1 policy-suppressed reference structure");
  assert.equal(policySuppressedLabel(530), "530 policy-suppressed reference structures");
});

test("Workspace and Project Globe render the secondary surface; primary cards are untouched", () => {
  const ws = readFileSync(new URL("../src/screens/production/Workspace.jsx", import.meta.url), "utf8");
  const globe = readFileSync(new URL("../src/screens/production/ProjectGlobe.jsx", import.meta.url), "utf8");
  assert.match(ws, /<PolicySuppressedReferences allocated=\{allocated\} openInspector=\{openInspector\} \/>/);
  assert.match(globe, /<PolicySuppressedReferences allocated=\{allocated\} openInspector=\{openInspector\} \/>/);
  assert.doesNotMatch(ws, /optimizer_scenarios_music_suppressed/, "Workspace cards never read the suppressed list");
});
