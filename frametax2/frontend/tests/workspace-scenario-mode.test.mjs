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
  const id = overrides.structure_id || "s1";
  return {
    structure_id: id,
    structure_type: "single_country",
    classification: "SINGLE_JURISDICTION",
    label: "Base",
    // Distinct by default (keyed off structure_id) so ordinary fixtures
    // never accidentally collide under the new canonical-identity dedup
    // — a test that WANTS a collision sets these explicitly.
    primary_jurisdiction: `JUR-${id}`,
    participants: [`JUR-${id}`],
    program_slugs: [`program-${id}`],
    economic_identity: null,
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

// ── WORKSPACE_VISUAL_REGRESSION_CORRECTION (2026-09-22) ───────────────────
// Canonical scenario deduplication — the real, confirmed defect: F#K
// Valentine's Day served FOUR distinct Ontario stacking permutations
// (different program combinations, different NPC) as four separate
// headline cards, crowding out every other jurisdiction/family. Fixed by
// collapsing to one canonical best (lowest-NPC, since rankOrNpcOrder
// already sorts ascending) scenario per identity — jurisdiction for
// Normal mode, full routed combination for Optimizer mode.

test("admissibleForMode (Normal): multiple stacking permutations of the SAME jurisdiction collapse to the single lowest-NPC one", () => {
  const structures = [
    structure({ structure_id: "on-a", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 2_556_030 }),
    structure({ structure_id: "on-b", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 3_043_784 }),
    structure({ structure_id: "on-c", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 3_055_697 }),
    structure({ structure_id: "on-d", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 3_321_377 }),
    structure({ structure_id: "mb", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-MB", npc_with_adjustments_usd: 3_183_390 }),
  ];
  const admissible = admissibleForMode(allocatedOf(structures), MODE_NORMAL);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["on-a", "mb"], (
    "only the lowest-NPC Ontario candidate (on-a) survives; on-b/c/d are the same jurisdiction, never four headline slots"
  ));
});

test("admissibleForMode (Optimizer): hybrids sharing the identical routed participants AND programs collapse to the single lowest-NPC one", () => {
  const structures = [
    structure({
      structure_id: "hy-1", classification: "HYBRID_ANCHOR_COMPONENT",
      participants: ["CA-MB", "CA-NL", "IT"], program_slugs: ["ca_mb_film_video_credit", "ca_nl_all_spend_credit", "it_tax_credit_foreign"],
      npc_with_adjustments_usd: 2_853_139,
    }),
    structure({
      structure_id: "hy-2", classification: "HYBRID_ANCHOR_COMPONENT",
      participants: ["IT", "CA-NL", "CA-MB"], program_slugs: ["it_tax_credit_foreign", "ca_mb_film_video_credit", "ca_nl_all_spend_credit"],
      npc_with_adjustments_usd: 2_859_952,
    }),
    structure({
      structure_id: "hy-3", classification: "HYBRID_ANCHOR_COMPONENT",
      participants: ["GR", "RO"], program_slugs: ["gr_cash_rebate", "ro_film_office_cash_rebate"],
      npc_with_adjustments_usd: 3_062_526,
    }),
  ];
  const admissible = admissibleForMode(allocatedOf(structures), MODE_OPTIMIZER);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["hy-1", "hy-3"], (
    "hy-2 is the SAME routed combination as hy-1 (order-independent) at a worse NPC -- collapsed; the genuinely distinct GR+RO hybrid (hy-3) is kept"
  ));
});

test("admissibleForMode: a real, non-null economic_identity is preferred over the jurisdiction/routing fallback key", () => {
  const structures = [
    structure({ structure_id: "e-1", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "CA-ON", economic_identity: "econ-abc", npc_with_adjustments_usd: 1 }),
    structure({ structure_id: "e-2", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "CA-ON", economic_identity: "econ-xyz", npc_with_adjustments_usd: 2 }),
  ];
  const admissible = admissibleForMode(allocatedOf(structures), MODE_NORMAL);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["e-1", "e-2"], (
    "two DIFFERENT real economic identities in the same jurisdiction are never collapsed just because the jurisdiction matches"
  ));
});

test("selectSixSlots: deduplicated distinct jurisdictions fill all six slots when enough real distinct scenarios exist", () => {
  const structures = [
    structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "US-GA", is_baseline: true, npc_with_adjustments_usd: 1 }),
    structure({ structure_id: "on-a", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 2 }),
    structure({ structure_id: "on-b", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 3 }),
    structure({ structure_id: "mb", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-MB", npc_with_adjustments_usd: 4 }),
    structure({ structure_id: "it", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "IT", npc_with_adjustments_usd: 5 }),
    structure({ structure_id: "gr", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "GR", npc_with_adjustments_usd: 6 }),
    structure({ structure_id: "nz", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "NZ", npc_with_adjustments_usd: 7 }),
  ];
  const { slots, leading, slot6 } = selectSixSlots(allocatedOf(structures), MODE_NORMAL, null);
  assert.equal(slots.length, 6);
  assert.deepEqual(leading.map((s) => s.structure_id), ["on-a", "mb", "it", "gr"]);
  assert.equal(slot6.structure_id, "nz");
});

test("family constants are the exact canonical values, never inferred/renamed", () => {
  assert.deepEqual(NORMAL_FAMILIES, ["SINGLE_JURISDICTION", "STACKED_PROGRAMS"]);
  assert.deepEqual(OPTIMIZER_FAMILIES, [
    "HYBRID_ANCHOR_COMPONENT", "OFFICIAL_COPRODUCTION", "COMBINED_COPRO_HYBRID_STACK", "MULTI_PRINCIPAL_MULTILATERAL",
  ]);
});
