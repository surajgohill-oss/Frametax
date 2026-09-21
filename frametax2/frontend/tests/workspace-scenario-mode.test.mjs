// ── Workspace scenario-mode data wiring — regression protection ──────────
//
// Run with: npm test (node --test)
//
// Pure logic tests for lib/workspaceScenarioMode.js — no JSX, no backend,
// no economics: every input below is a hand-built structure entry shaped
// like the real allocated_structures payload (canonical_production_view.py's
// own `classification` field — app/services/structural_classification.py's
// canonical enum). Every assertion checks SELECTION only: which structures
// occupy which of the six Workspace slots for a given mode, never a
// re-derivation of family/classification.

import test from "node:test";
import assert from "node:assert/strict";
import {
  MODE_NORMAL,
  MODE_OPTIMIZER,
  NORMAL_FAMILIES,
  OPTIMIZER_FAMILIES,
  admissibleForMode,
  selectSixSlots,
} from "../src/lib/workspaceScenarioMode.js";

function structure(overrides) {
  return {
    structure_id: "s1",
    structure_type: "single_country",
    classification: "SINGLE_JURISDICTION",
    label: "Base",
    primary_jurisdiction: "US",
    is_fully_priced: true,
    is_baseline: false,
    npc_with_adjustments_usd: 900_000,
    segments: [],
    ...overrides,
  };
}

function allocatedOf(structures) {
  return { structures, ranking: [] };
}

test("admissibleForMode: Normal mode admits only SINGLE_JURISDICTION and STACKED_PROGRAMS classifications", () => {
  const structures = [
    structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", is_baseline: true, npc_with_adjustments_usd: 1 }),
    structure({ structure_id: "stack", classification: "STACKED_PROGRAMS", npc_with_adjustments_usd: 2 }),
    structure({ structure_id: "hybrid", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 3 }),
    structure({ structure_id: "treaty", classification: "OFFICIAL_COPRODUCTION", npc_with_adjustments_usd: 4 }),
    structure({ structure_id: "combined", classification: "COMBINED_COPRO_HYBRID_STACK", npc_with_adjustments_usd: 5 }),
    structure({ structure_id: "multilateral", classification: "MULTI_PRINCIPAL_MULTILATERAL", npc_with_adjustments_usd: 6 }),
  ];
  const admissible = admissibleForMode(allocatedOf(structures), MODE_NORMAL);
  assert.deepEqual(admissible.map((s) => s.structure_id).sort(), ["anchor", "stack"]);
});

test("admissibleForMode: Optimizer mode admits every component/co-production/multilateral family, never SINGLE_JURISDICTION/STACKED_PROGRAMS", () => {
  const structures = [
    structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", is_baseline: true, npc_with_adjustments_usd: 1 }),
    structure({ structure_id: "stack", classification: "STACKED_PROGRAMS", npc_with_adjustments_usd: 2 }),
    structure({ structure_id: "hybrid", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 3 }),
    structure({ structure_id: "treaty", classification: "OFFICIAL_COPRODUCTION", npc_with_adjustments_usd: 4 }),
    structure({ structure_id: "combined", classification: "COMBINED_COPRO_HYBRID_STACK", npc_with_adjustments_usd: 5 }),
    structure({ structure_id: "multilateral", classification: "MULTI_PRINCIPAL_MULTILATERAL", npc_with_adjustments_usd: 6 }),
  ];
  const admissible = admissibleForMode(allocatedOf(structures), MODE_OPTIMIZER);
  assert.deepEqual(
    admissible.map((s) => s.structure_id).sort(),
    ["combined", "hybrid", "multilateral", "treaty"],
  );
});

test("admissibleForMode: never admits a rejected/authority-insufficient/unresolved candidate into either mode", () => {
  const structures = [
    structure({ structure_id: "priced-normal", classification: "SINGLE_JURISDICTION", npc_with_adjustments_usd: 1 }),
    structure({ structure_id: "rejected", classification: "REJECTED_FOR_PROJECT", is_fully_priced: false, npc_with_adjustments_usd: null }),
    structure({ structure_id: "authority-locked", classification: "AUTHORITY_LOCKED", is_fully_priced: false, npc_with_adjustments_usd: null }),
    structure({ structure_id: "rule-incomplete", classification: "RULE_DATA_INCOMPLETE", is_fully_priced: false, npc_with_adjustments_usd: null }),
  ];
  assert.deepEqual(admissibleForMode(allocatedOf(structures), MODE_NORMAL).map((s) => s.structure_id), ["priced-normal"]);
  assert.deepEqual(admissibleForMode(allocatedOf(structures), MODE_OPTIMIZER).map((s) => s.structure_id), []);
});

test("admissibleForMode: Optimizer mode appends conditional grant/fund opportunities strictly after every priced candidate", () => {
  const structures = [
    structure({ structure_id: "hybrid-1", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 2 }),
    structure({ structure_id: "opportunity", classification: "CONDITIONAL_USER_FACT_REQUIRED", is_fully_priced: false, npc_with_adjustments_usd: null }),
  ];
  const admissible = admissibleForMode(allocatedOf(structures), MODE_OPTIMIZER);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["hybrid-1", "opportunity"]);
});

test("selectSixSlots: Current Location (the anchor) never changes between modes", () => {
  const structures = [
    structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", is_baseline: true, npc_with_adjustments_usd: 1 }),
    structure({ structure_id: "hybrid-1", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 2 }),
    structure({ structure_id: "stack-1", classification: "STACKED_PROGRAMS", npc_with_adjustments_usd: 3 }),
  ];
  const allocated = allocatedOf(structures);
  const normal = selectSixSlots(allocated, MODE_NORMAL, null);
  const optimizer = selectSixSlots(allocated, MODE_OPTIMIZER, null);
  assert.equal(normal.anchor.structure_id, "anchor");
  assert.equal(optimizer.anchor.structure_id, "anchor");
});

test("selectSixSlots: slots 2-5 are the top four mode-admissible scenarios, excluding the anchor, in canonical rank/NPC order", () => {
  const structures = [
    structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", is_baseline: true, npc_with_adjustments_usd: 1 }),
    ...["a", "b", "c", "d", "e", "f"].map((id, i) =>
      structure({ structure_id: `hybrid-${id}`, classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 10 + i }),
    ),
  ];
  const { leading } = selectSixSlots(allocatedOf(structures), MODE_OPTIMIZER, null);
  assert.deepEqual(leading.map((s) => s.structure_id), ["hybrid-a", "hybrid-b", "hybrid-c", "hybrid-d"]);
});

test("selectSixSlots: slot 6 defaults to the canonical rank-5 admissible candidate when no override is stored", () => {
  const structures = [
    structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", is_baseline: true, npc_with_adjustments_usd: 1 }),
    ...["a", "b", "c", "d", "e", "f"].map((id, i) =>
      structure({ structure_id: `hybrid-${id}`, classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 10 + i }),
    ),
  ];
  const { slot6, dropdownOptions } = selectSixSlots(allocatedOf(structures), MODE_OPTIMIZER, null);
  assert.equal(slot6.structure_id, "hybrid-e");
  assert.deepEqual(dropdownOptions.map((s) => s.structure_id), ["hybrid-e", "hybrid-f"]);
});

test("selectSixSlots: a stored slot-6 override selects that candidate instead of the default rank-5", () => {
  const structures = [
    structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", is_baseline: true, npc_with_adjustments_usd: 1 }),
    ...["a", "b", "c", "d", "e", "f"].map((id, i) =>
      structure({ structure_id: `hybrid-${id}`, classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 10 + i }),
    ),
  ];
  const { slot6 } = selectSixSlots(allocatedOf(structures), MODE_OPTIMIZER, "hybrid-f");
  assert.equal(slot6.structure_id, "hybrid-f");
});

test("selectSixSlots: fewer than six real candidates is a valid, honest result — nothing is fabricated", () => {
  const structures = [
    structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", is_baseline: true, npc_with_adjustments_usd: 1 }),
    structure({ structure_id: "stack-1", classification: "STACKED_PROGRAMS", npc_with_adjustments_usd: 2 }),
  ];
  const { slots, slot6, dropdownOptions } = selectSixSlots(allocatedOf(structures), MODE_NORMAL, null);
  assert.equal(slots.length, 2);
  assert.equal(slot6, null);
  assert.deepEqual(dropdownOptions, []);
});

test("family constants are the exact canonical values, never inferred/renamed", () => {
  assert.deepEqual(NORMAL_FAMILIES, ["SINGLE_JURISDICTION", "STACKED_PROGRAMS"]);
  assert.deepEqual(OPTIMIZER_FAMILIES, [
    "HYBRID_ANCHOR_COMPONENT", "OFFICIAL_COPRODUCTION", "COMBINED_COPRO_HYBRID_STACK", "MULTI_PRINCIPAL_MULTILATERAL",
  ]);
});
