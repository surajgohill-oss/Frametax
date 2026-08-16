// ── Overview UI contract — Production Options regression protection ──────
//
// Run with: npm test (node --test)
//
// Pure logic tests for lib/productionOptions.js (classification + Top Six
// selection) — no JSX, no backend, no economics: every input below is a
// hand-built structure entry shaped like the real allocated_structures
// payload (canonical_production_view.py / little_utopia_state.py), and
// every assertion checks DISPLAY selection/labeling only.

import test from "node:test";
import assert from "node:assert/strict";
import { classifyStructure, selectTopOptions, isDirectlyComparable, CLASSIFICATIONS } from "../src/lib/productionOptions.js";

function structure(overrides) {
  return {
    structure_id: "s1",
    structure_type: "single_country",
    label: "Base",
    primary_jurisdiction: "US",
    participants: ["US"],
    is_fully_priced: true,
    is_baseline: false,
    treaty_slug: null,
    gross_budget_usd: 1_000_000,
    selected_incentive_usd: 100_000,
    npc_with_adjustments_usd: 900_000,
    segments: [],
    ...overrides,
  };
}

test("classifyStructure: structure_type 'single_country' alone (is_baseline false/absent) is still Current — little_utopia_state.py's own per-structure dict never carries is_baseline", () => {
  // Real bug found live: LU's rich structures endpoint has no is_baseline
  // key whatsoever (only canonical_production_view.py's generic path
  // does), so classifyStructure must not depend on it being present or true.
  const s = structure({ structure_type: "single_country", is_baseline: false });
  assert.equal(classifyStructure(s).key, "current");
});

test("classifyStructure: baseline is always Current / Base Production, regardless of other fields", () => {
  const s = structure({ is_baseline: true, structure_type: "full_relocation", treaty_slug: "eurimages" });
  assert.equal(classifyStructure(s).key, "current");
});

test("classifyStructure: treaty_slug presence is the ONLY signal for Official Treaty Co-Production", () => {
  const withTreaty = structure({ treaty_slug: "european-convention-coproduction", structure_type: "dual_country" });
  assert.equal(classifyStructure(withTreaty).key, "treaty");
  assert.equal(classifyStructure(withTreaty).label, "Official Treaty Co-Production");
});

test("classifyStructure: a plain two-participant structure with NO treaty_slug is Hybrid / Component, never Treaty", () => {
  const split = structure({ structure_type: "component_relocation", participants: ["GR", "AU"], treaty_slug: null });
  assert.equal(classifyStructure(split).key, "hybrid");
  assert.notEqual(classifyStructure(split).key, "treaty");
});

test("classifyStructure: full_relocation without a treaty is Full Relocation", () => {
  const reloc = structure({ structure_type: "full_relocation", treaty_slug: null });
  assert.equal(classifyStructure(reloc).key, "relocation");
});

// Critical LU regression guard: little_utopia_state.py's own
// rank_allocated_structures() ranking entries have NO is_directly_comparable
// field at all (only canonical_production_view.py's generic path sets it).
// Without a fallback, LU's Scenarios page would suddenly show ZERO
// comparable columns and dump its entire ranked universe into Review.
test("isDirectlyComparable: falls back to is_fully_priced when the field is absent (little_utopia_state.py's own ranking shape)", () => {
  assert.equal(isDirectlyComparable({ is_fully_priced: true }), true);
  assert.equal(isDirectlyComparable({ is_fully_priced: false }), false);
});

test("isDirectlyComparable: an explicit is_directly_comparable field (canonical_production_view.py's generic path) always wins over is_fully_priced", () => {
  assert.equal(isDirectlyComparable({ is_fully_priced: true, is_directly_comparable: false }), false);
  assert.equal(isDirectlyComparable({ is_fully_priced: false, is_directly_comparable: true }), true);
});

test("selectTopOptions: returns at most 6, in the existing ranking order, never invents options", () => {
  const structures = Array.from({ length: 8 }, (_, i) => structure({ structure_id: `s${i}`, is_baseline: i === 0 }));
  const ranking = structures.map((s, i) => ({ structure_id: s.structure_id, is_fully_priced: true, is_directly_comparable: true, rank: i + 1 }));
  const allocated = { structures, ranking };
  const options = selectTopOptions(allocated);
  assert.equal(options.length, 6);
  assert.deepEqual(options.map((o) => o.structure_id), ["s0", "s1", "s2", "s3", "s4", "s5"]);
});

test("selectTopOptions: fewer than 6 valid options never gets padded", () => {
  const structures = [structure({ structure_id: "a", is_baseline: true }), structure({ structure_id: "b" })];
  const ranking = structures.map((s) => ({ structure_id: s.structure_id, is_fully_priced: true, is_directly_comparable: true }));
  const options = selectTopOptions({ structures, ranking });
  assert.equal(options.length, 2);
});

test("selectTopOptions: unpriced/unavailable structures never occupy a Top 6 slot", () => {
  const priced = Array.from({ length: 5 }, (_, i) => structure({ structure_id: `p${i}`, is_baseline: i === 0 }));
  const unpriced = structure({ structure_id: "unpriced", is_fully_priced: false });
  const ranking = [
    ...priced.map((s) => ({ structure_id: s.structure_id, is_fully_priced: true, is_directly_comparable: true })),
    { structure_id: "unpriced", is_fully_priced: false, is_directly_comparable: false },
  ];
  const options = selectTopOptions({ structures: [...priced, unpriced], ranking });
  assert.ok(!options.some((o) => o.structure_id === "unpriced"), "unpriced structure must never appear in the Top 6");
});

// Canonical served wiring repair (Codex Defect 2): a structure that IS
// priced but is NOT regionally comparable must also stay out of the Top
// 6 -- comparability, not priceability, gates this selection. Its real
// economics still exist (see Scenarios.jsx's Review section), just not
// promoted into the primary comparison here.
test("selectTopOptions: priced-but-not-comparable structures never occupy a Top 6 slot either", () => {
  const comparable = Array.from({ length: 3 }, (_, i) => structure({ structure_id: `c${i}`, is_baseline: i === 0 }));
  const reviewRequired = structure({ structure_id: "review1", is_fully_priced: true, npc_with_adjustments_usd: 1 });
  const ranking = [
    ...comparable.map((s) => ({ structure_id: s.structure_id, is_fully_priced: true, is_directly_comparable: true })),
    { structure_id: "review1", is_fully_priced: true, is_directly_comparable: false },
  ];
  const options = selectTopOptions({ structures: [...comparable, reviewRequired], ranking });
  assert.ok(!options.some((o) => o.structure_id === "review1"), "priced-but-not-comparable structure must never appear in the Top 6");
});

test("selectTopOptions: sixth slot promotes an explicit treaty structure not already in the first five", () => {
  const firstFive = Array.from({ length: 5 }, (_, i) => structure({ structure_id: `r${i}`, is_baseline: i === 0 }));
  const treatyCandidate = structure({ structure_id: "treaty1", treaty_slug: "ibermedia-multilateral", npc_with_adjustments_usd: 500_000 });
  const sixthInOrder = structure({ structure_id: "r5" });
  const ranking = [
    ...firstFive.map((s) => ({ structure_id: s.structure_id, is_fully_priced: true, is_directly_comparable: true })),
    { structure_id: "r5", is_fully_priced: true, is_directly_comparable: true },
    { structure_id: "treaty1", is_fully_priced: true, is_directly_comparable: true },
  ];
  const options = selectTopOptions({ structures: [...firstFive, sixthInOrder, treatyCandidate], ranking });
  assert.equal(options.length, 6);
  assert.equal(options[5].structure_id, "treaty1", "an explicit treaty candidate must win the sixth slot over the next plain option");
});

test("selectTopOptions: with no treaty candidate available, the sixth slot falls back to the next existing ranked option", () => {
  const six = Array.from({ length: 6 }, (_, i) => structure({ structure_id: `n${i}`, is_baseline: i === 0 }));
  const ranking = six.map((s) => ({ structure_id: s.structure_id, is_fully_priced: true, is_directly_comparable: true }));
  const options = selectTopOptions({ structures: six, ranking });
  assert.equal(options.length, 6);
  assert.equal(options[5].structure_id, "n5");
});
