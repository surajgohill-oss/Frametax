// ── Workspace scenario-mode data wiring — regression protection ──────────
//
// Run with: npm test (node --test)
//
// Pure logic tests for lib/workspaceScenarioMode.js — no JSX, no backend,
// no economics: every input below is a hand-built structure entry shaped
// like the real allocated_structures payload (canonical_production_view.py's
// own `classification`/`best_per_jurisdiction` fields). Every assertion
// checks SELECTION only: which structures occupy which of the six
// Workspace slots for a given mode.
//
// WORKSPACE_CANONICAL_JURISDICTION_WINNERS (2026-09-21): Single
// Jurisdiction mode now consumes the backend's own canonical
// `best_per_jurisdiction` projection directly (one entry per jurisdiction,
// already deduplicated/ranked server-side) instead of reconstructing
// jurisdiction winners client-side from the bounded `structures` page —
// the root cause of the earlier duplicate/missing-jurisdiction defect
// (see the module's own header comment for the full trace).

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
    primary_jurisdiction: `JUR-${id}`,
    participants: [`JUR-${id}`],
    program_slugs: [`program-${id}`],
    // COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21): every real,
    // priced structure the backend ever serves carries its own real,
    // distinct economic_identity (confirmed live across all four
    // productions: 0 nulls, 0 duplicates) — default to a per-fixture
    // unique value here rather than null, so a test that does not care
    // about economic_identity does not accidentally exercise a dedup
    // collision it never intended.
    economic_identity: `econ-${id}`,
    is_fully_priced: true,
    is_baseline: false,
    npc_with_adjustments_usd: 900_000,
    segments: [],
    ...overrides,
  };
}

// best_per_jurisdiction fixture builder — the SAME real shape
// canonical_production_view.py now serves (the full structure entry plus
// economic_identity), keyed by jurisdiction code.
function bestPerJurisdiction(entries) {
  const out = {};
  for (const e of entries) out[e.primary_jurisdiction] = e;
  return out;
}

// COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21): `optimizer_candidates`
// fixture builder — mirrors canonical_production_view.py's own construction
// exactly (filter to OPTIMIZER_FAMILIES + is_fully_priced, ascending NPC,
// already deduplicated by economic_identity server-side) so every existing
// Optimizer-mode fixture below keeps working by simply listing its
// structures once, the same as it already does for Single Jurisdiction via
// best_per_jurisdiction.
function optimizerCandidatesOf(entries) {
  return [...entries]
    .filter((s) => OPTIMIZER_FAMILIES.includes(s.classification) && s.is_fully_priced)
    .sort((a, b) => (a.npc_with_adjustments_usd ?? Infinity) - (b.npc_with_adjustments_usd ?? Infinity));
}

function allocatedOf(structures, bpjEntries, optimizerEntries, optimizerScenarios) {
  const candidates = optimizerEntries ?? optimizerCandidatesOf(structures);
  return {
    structures,
    ranking: [],
    best_per_jurisdiction: bestPerJurisdiction(bpjEntries ?? structures.filter((s) => NORMAL_FAMILIES.includes(s.classification))),
    optimizer_candidates: candidates,
    // PRODUCER_OPTIMIZER_SCENARIO_CANONICALIZATION (2026-09-21): unit
    // fixtures build one hand-crafted structure per conceptual route, so the
    // scenario projection equals the candidate pool by default — the real
    // backend grouping/collapse logic is pinned separately against live
    // data in test_canonical_production_view.py.
    optimizer_scenarios: optimizerScenarios ?? candidates,
  };
}

test("admissibleForMode (Single Jurisdiction): consumes best_per_jurisdiction directly — one entry per jurisdiction, already the canonical winner", () => {
  const anchor = structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "GR", is_baseline: true, npc_with_adjustments_usd: 1 });
  const on = structure({ structure_id: "on-winner", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 2_556_030 });
  const mb = structure({ structure_id: "mb-winner", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "CA-MB", npc_with_adjustments_usd: 3_183_389 });
  const allocated = allocatedOf([anchor, on, mb]);
  const admissible = admissibleForMode(allocated, MODE_NORMAL);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["anchor", "on-winner", "mb-winner"]);
});

test("admissibleForMode (Single Jurisdiction): multiple Ontario candidate permutations collapse into the single canonical best-NPC Ontario winner", () => {
  // Four REAL, distinct Ontario program-stack permutations (like F#K
  // Valentine's Day's own data) never reach admissibleForMode as raw
  // candidates at all here — best_per_jurisdiction has ALREADY reduced
  // them, server-side, to their one canonical winner (on_ofttc+ocase,
  // the lowest-NPC of the four). This fixture proves the frontend trusts
  // that reduction rather than re-deriving it from raw permutations.
  const onWinner = structure({
    structure_id: "on-ofttc-ocase", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON",
    label: "Ontario — OFTTC + OCASE (combined)", program_slugs: ["on_ofttc", "ontario_computer_animation_and_special_effects_tax_credit_ocase"],
    npc_with_adjustments_usd: 2_556_030.86,
  });
  const mb = structure({ structure_id: "mb", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "CA-MB", npc_with_adjustments_usd: 3_183_389.9 });
  const allocated = allocatedOf([onWinner, mb], [onWinner, mb]);
  const admissible = admissibleForMode(allocated, MODE_NORMAL);
  const ontario = admissible.filter((s) => s.primary_jurisdiction === "CA-ON");
  assert.equal(ontario.length, 1, "exactly one Ontario headline entry, never several permutations");
  assert.equal(ontario[0].structure_id, "on-ofttc-ocase");
  assert.equal(ontario[0].npc_with_adjustments_usd, 2_556_030.86, "the winner is the canonical best-NPC executable Ontario outcome");
  assert.match(ontario[0].label, /OFTTC \+ OCASE/, "the winning stack's contributing programs remain disclosed in the label");
});

test("admissibleForMode (Single Jurisdiction): ordered by canonical NPC ascending, never re-ranked by geography/diversity", () => {
  const a = structure({ structure_id: "a", primary_jurisdiction: "AA", npc_with_adjustments_usd: 300 });
  const b = structure({ structure_id: "b", primary_jurisdiction: "BB", npc_with_adjustments_usd: 100 });
  const c = structure({ structure_id: "c", primary_jurisdiction: "CC", npc_with_adjustments_usd: 200 });
  const allocated = allocatedOf([a, b, c], [a, b, c]);
  const admissible = admissibleForMode(allocated, MODE_NORMAL);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["b", "c", "a"]);
});

// PRODUCER_OPTIMIZER_SCENARIO_CANONICALIZATION (2026-09-21): admissibleForMode
// must read the canonical `optimizer_scenarios` projection, never the raw
// `optimizer_candidates` collection — even when both are present and differ
// (the exact live shape: optimizer_candidates has 3 raw Manitoba+NL+Italy
// iterations, optimizer_scenarios has already collapsed them to 1).
test("admissibleForMode (Optimizer): reads allocated.optimizer_scenarios, never the raw optimizer_candidates collection", () => {
  const rawA = structure({ structure_id: "raw-a", classification: "HYBRID_ANCHOR_COMPONENT", economic_identity: "econ-a", npc_with_adjustments_usd: 1 });
  const rawB = structure({ structure_id: "raw-b", classification: "HYBRID_ANCHOR_COMPONENT", economic_identity: "econ-b", npc_with_adjustments_usd: 2 });
  const rawC = structure({ structure_id: "raw-c", classification: "HYBRID_ANCHOR_COMPONENT", economic_identity: "econ-c", npc_with_adjustments_usd: 3 });
  const scenarioRep = { ...rawA, raw_variant_count: 3, raw_variant_structure_ids: ["raw-a", "raw-b", "raw-c"] };
  const allocated = {
    structures: [rawA, rawB, rawC], ranking: [], best_per_jurisdiction: {},
    optimizer_candidates: [rawA, rawB, rawC],
    optimizer_scenarios: [scenarioRep],
  };
  const admissible = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["raw-a"], "must resolve through optimizer_scenarios (1 collapsed entry), never the 3 raw candidates");
  assert.equal(admissible[0].raw_variant_count, 3);
});

test("admissibleForMode (Optimizer): every canonical multi-jurisdiction family is admitted, single-jurisdiction families are not", () => {
  const structures = [
    structure({ structure_id: "stack", classification: "STACKED_PROGRAMS", npc_with_adjustments_usd: 2 }),
    structure({ structure_id: "hybrid", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 3 }),
    structure({ structure_id: "treaty", classification: "OFFICIAL_COPRODUCTION", npc_with_adjustments_usd: 4 }),
    structure({ structure_id: "combined", classification: "COMBINED_COPRO_HYBRID_STACK", npc_with_adjustments_usd: 5 }),
    structure({ structure_id: "multilateral", classification: "MULTI_PRINCIPAL_MULTILATERAL", npc_with_adjustments_usd: 6 }),
  ];
  const admissible = admissibleForMode(allocatedOf(structures, []), MODE_OPTIMIZER);
  assert.deepEqual(
    admissible.map((s) => s.structure_id).sort(),
    ["combined", "hybrid", "multilateral", "treaty"],
  );
});

// COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21) — ROOT CAUSE regression
// guard: the OLD admissibleForMode read `allocated.structures` (bounded to
// 100 across ALL families) plus `allocated.top_by_structural_family`
// (bounded to TYPE_TOP=100 PER family) as a "family entirely absent"
// backstop — which never helped a family that WAS represented, just
// incompletely. Confirmed live for F#K Valentine's Day: 411 real PRICED
// HYBRID_ANCHOR_COMPONENT candidates, of which only 93 ever reached the
// page. This fixture reproduces that shape at a smaller scale (150 real
// candidates in one family, far past the old 100-per-family cap) and
// proves every one is now reachable, since `optimizer_candidates` itself
// is never capped.
test("admissibleForMode (Optimizer): a family with more than 100 real priced candidates is served completely, never capped at the old page/backstop limit", () => {
  const many = Array.from({ length: 150 }, (_, i) =>
    structure({
      structure_id: `hybrid-${i}`, classification: "HYBRID_ANCHOR_COMPONENT",
      economic_identity: `econ-hybrid-${i}`, npc_with_adjustments_usd: 1000 + i,
    }));
  const admissible = admissibleForMode(allocatedOf(many, []), MODE_OPTIMIZER);
  assert.equal(admissible.length, 150, "every one of the 150 real priced optimizer candidates must be reachable");
  assert.equal(new Set(admissible.map((s) => s.economic_identity)).size, 150);
});

// COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21) — supersedes the two
// tests this replaces (both pinned a client-side participants/programs
// collapse heuristic that no longer exists): admissibleForMode's Optimizer
// branch now reads `allocated.optimizer_candidates` verbatim — the
// backend's own complete, already-deduplicated-by-economic_identity
// projection (canonical_production_view.py) — never re-deriving its own
// dedup/collapse rule. Two structures sharing identical participants AND
// programs but DIFFERENT real economic identities (a real, legitimate
// case: several of F#K Valentine's Day's hybrid candidates share a routed
// combination at a few dollars' rounding difference) must both survive —
// collapsing them client-side was the old, now-removed behavior.
test("admissibleForMode (Optimizer): reads allocated.optimizer_candidates verbatim — no client-side collapse by shared participants/programs, only the backend's own economic_identity dedup", () => {
  const structures = [
    structure({
      structure_id: "hy-1", classification: "HYBRID_ANCHOR_COMPONENT", economic_identity: "econ-abc",
      participants: ["CA-MB", "CA-NL", "IT"], program_slugs: ["ca_mb_film_video_credit", "ca_nl_all_spend_credit", "it_tax_credit_foreign"],
      npc_with_adjustments_usd: 2_853_139,
    }),
    structure({
      structure_id: "hy-2", classification: "HYBRID_ANCHOR_COMPONENT", economic_identity: "econ-xyz",
      participants: ["CA-MB", "CA-NL", "IT"], program_slugs: ["ca_mb_film_video_credit", "ca_nl_all_spend_credit", "it_tax_credit_foreign"],
      npc_with_adjustments_usd: 2_859_952,
    }),
  ];
  const admissible = admissibleForMode(allocatedOf(structures, []), MODE_OPTIMIZER);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["hy-1", "hy-2"], (
    "hy-1 and hy-2 share identical participants and programs but carry two DIFFERENT real economic " +
    "identities -- both must be reachable, never collapsed to one just because the routing looks the same"
  ));
});

test("admissibleForMode (Optimizer): conditional grant/fund opportunities are appended strictly after every priced candidate", () => {
  const structures = [
    structure({ structure_id: "hybrid-1", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 2 }),
    structure({ structure_id: "opportunity", classification: "CONDITIONAL_USER_FACT_REQUIRED", is_fully_priced: false, npc_with_adjustments_usd: null }),
  ];
  const admissible = admissibleForMode(allocatedOf(structures, []), MODE_OPTIMIZER);
  assert.deepEqual(admissible.map((s) => s.structure_id), ["hybrid-1", "opportunity"]);
});

test("selectSixSlots: the original/as-ingested scenario (Current Location) is always slot 1 and never changes between modes", () => {
  const anchor = structure({ structure_id: "anchor", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "GR", is_baseline: true, npc_with_adjustments_usd: 1 });
  const hybrid1 = structure({ structure_id: "hybrid-1", classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 2 });
  const stack1 = structure({ structure_id: "stack-1", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 3 });
  const allocated = allocatedOf([anchor, hybrid1, stack1], [anchor, stack1]);
  const normal = selectSixSlots(allocated, MODE_NORMAL, null);
  const optimizer = selectSixSlots(allocated, MODE_OPTIMIZER, null);
  assert.equal(normal.anchor.structure_id, "anchor");
  assert.equal(optimizer.anchor.structure_id, "anchor");
});

test("selectSixSlots (Single Jurisdiction): five unique jurisdiction winners populate slots 2-6 in canonical NPC order, slot 6 defaults to rank 5", () => {
  const anchor = structure({ structure_id: "anchor", primary_jurisdiction: "US-GA", is_baseline: true, npc_with_adjustments_usd: 1 });
  const winners = ["CA-ON", "CA-MB", "IT", "GR", "NZ", "FR"].map((jur, i) =>
    structure({ structure_id: `w-${jur}`, primary_jurisdiction: jur, npc_with_adjustments_usd: 10 + i }),
  );
  const allocated = allocatedOf([anchor, ...winners], [anchor, ...winners]);
  const { slots, leading, slot6, dropdownOptions } = selectSixSlots(allocated, MODE_NORMAL, null);
  assert.equal(slots.length, 6);
  assert.equal(slots[0].structure_id, "anchor");
  assert.deepEqual(leading.map((s) => s.primary_jurisdiction), ["CA-ON", "CA-MB", "IT", "GR"]);
  assert.equal(slot6.primary_jurisdiction, "NZ");
  assert.deepEqual(dropdownOptions.map((s) => s.primary_jurisdiction), ["NZ", "FR"]);
  const jurisdictions = slots.map((s) => s.primary_jurisdiction);
  assert.equal(new Set(jurisdictions).size, jurisdictions.length, "no jurisdiction repeats across the six headline slots");
});

test("selectSixSlots (Single Jurisdiction): slot-6 dropdown contains every remaining unique jurisdiction not already in slots 1-5, with no duplicates", () => {
  const anchor = structure({ structure_id: "anchor", primary_jurisdiction: "US-GA", is_baseline: true, npc_with_adjustments_usd: 1 });
  const winners = ["CA-ON", "CA-MB", "IT", "GR", "NZ", "FR", "AU"].map((jur, i) =>
    structure({ structure_id: `w-${jur}`, primary_jurisdiction: jur, npc_with_adjustments_usd: 10 + i }),
  );
  const allocated = allocatedOf([anchor, ...winners], [anchor, ...winners]);
  const { anchor: slot1, leading, dropdownOptions } = selectSixSlots(allocated, MODE_NORMAL, null);
  // Slots 1-5 (anchor + the top four) must never reappear in the dropdown
  // — the dropdown replaces ONLY slot 6, so it is scoped to every
  // remaining candidate AFTER rank 4, which by construction includes the
  // current slot 6 itself (the same "current item also selectable"
  // contract the pre-existing Other Scenarios control already used).
  const shownInSlots1to5 = new Set([slot1.primary_jurisdiction, ...leading.map((s) => s.primary_jurisdiction)]);
  for (const opt of dropdownOptions) assert.equal(shownInSlots1to5.has(opt.primary_jurisdiction), false);
  const dropdownJurisdictions = dropdownOptions.map((s) => s.primary_jurisdiction);
  assert.equal(new Set(dropdownJurisdictions).size, dropdownJurisdictions.length, "no duplicate jurisdictions in the dropdown");
  assert.deepEqual(dropdownJurisdictions, ["NZ", "FR", "AU"]);
});

test("selectSixSlots: a stored slot-6 override selects that candidate instead of the default rank-5", () => {
  const anchor = structure({ structure_id: "anchor", is_baseline: true, npc_with_adjustments_usd: 1 });
  const winners = ["a", "b", "c", "d", "e", "f"].map((id, i) =>
    structure({ structure_id: `hybrid-${id}`, classification: "HYBRID_ANCHOR_COMPONENT", npc_with_adjustments_usd: 10 + i }),
  );
  const allocated = allocatedOf([anchor, ...winners], [anchor]);
  const { slot6 } = selectSixSlots(allocated, MODE_OPTIMIZER, "hybrid-f");
  assert.equal(slot6.structure_id, "hybrid-f");
});

// PRODUCER_OPTIMIZER_PRESENTATION_CORRECTION (2026-09-22): canonical_production_
// view.py now serves `optimizer_scenarios` PRE-SORTED Practical -> Formal ->
// Advanced (ascending NPC within each tier) — admissibleForMode/selectSixSlots
// consume that order verbatim, with no client-side re-sort. This fixture
// mirrors that real served shape (a Practical tier or two, then Advanced) and
// proves Workspace's headline cards/dropdown correctly inherit it: Practical
// scenarios fill the leading slots first, Advanced scenarios only appear once
// Practical is exhausted, and every remaining scenario (of either tier) stays
// reachable in the dropdown.
test("selectSixSlots (Optimizer): Practical-tier scenarios fill the leading slots before any Advanced scenario, matching the backend's pre-sorted order", () => {
  const anchor = structure({ structure_id: "anchor", is_baseline: true, npc_with_adjustments_usd: 1 });
  // 3 Practical (2-jurisdiction) scenarios, cheaper overall, then 2 Advanced
  // (3+-jurisdiction) scenarios that are even CHEAPER by NPC alone — proving
  // the tier partition wins over a naive NPC-only sort, exactly like the
  // real backend's tier-then-NPC key.
  const practical = ["p1", "p2", "p3"].map((id, i) => structure({
    structure_id: id, classification: "HYBRID_ANCHOR_COMPONENT", participants: ["GR", `X${i}`],
    npc_with_adjustments_usd: 100 + i, practicality_tier: "PRACTICAL_HYBRID", participant_count: 2,
  }));
  const advanced = ["a1", "a2"].map((id, i) => structure({
    structure_id: id, classification: "HYBRID_ANCHOR_COMPONENT", participants: ["GR", "CA-MB", "IT"],
    npc_with_adjustments_usd: 10 + i, practicality_tier: "ADVANCED_MULTI_JURISDICTION", participant_count: 3,
  }));
  // Pre-sorted the way canonical_production_view.py serves it: Practical
  // (ascending NPC), then Advanced (ascending NPC) — NOT plain NPC order.
  const preSorted = [...practical, ...advanced];
  const allocated = { structures: [anchor, ...preSorted], ranking: [], best_per_jurisdiction: {}, optimizer_scenarios: preSorted };
  const { leading, slot6, dropdownOptions } = selectSixSlots(allocated, MODE_OPTIMIZER, null);
  assert.deepEqual(leading.map((s) => s.structure_id), ["p1", "p2", "p3", "a1"], "the 3 Practical scenarios must fill first, an Advanced one only after Practical is exhausted, never re-sorted by NPC alone");
  assert.equal(slot6.structure_id, "a2");
  assert.deepEqual(dropdownOptions.map((s) => s.structure_id), ["a2"], "every remaining scenario, Practical or Advanced, must stay reachable in the dropdown");
});

test("selectSixSlots: fewer than six real distinct jurisdiction winners is a valid, honest result — never backfilled with a duplicate", () => {
  const anchor = structure({ structure_id: "anchor", primary_jurisdiction: "US-GA", is_baseline: true, npc_with_adjustments_usd: 1 });
  const on = structure({ structure_id: "on", classification: "STACKED_PROGRAMS", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 2 });
  const allocated = allocatedOf([anchor, on], [anchor, on]);
  const { slots, slot6, dropdownOptions } = selectSixSlots(allocated, MODE_NORMAL, null);
  assert.equal(slots.length, 2);
  assert.equal(slot6, null);
  assert.deepEqual(dropdownOptions, []);
});

test("an arbitrary new/synthetic project (no special-casing) uses the identical best_per_jurisdiction projection and six-slot wiring", () => {
  // No hardcoded production id/name anywhere in workspaceScenarioMode.js
  // — this fixture is deliberately a project this module has never seen,
  // proving the wiring is generic.
  const anchor = structure({ structure_id: "brand-new-anchor", primary_jurisdiction: "PT", is_baseline: true, npc_with_adjustments_usd: 1 });
  const singleJurStack = structure({ structure_id: "brand-new-stack", classification: "STACKED_PROGRAMS", primary_jurisdiction: "HR", npc_with_adjustments_usd: 2 });
  const hybrid = structure({ structure_id: "brand-new-hybrid", classification: "HYBRID_ANCHOR_COMPONENT", participants: ["PT", "HR"], program_slugs: ["pt_x", "hr_y"], npc_with_adjustments_usd: 3 });
  const allocated = allocatedOf([anchor, singleJurStack, hybrid], [anchor, singleJurStack]);
  const normal = selectSixSlots(allocated, MODE_NORMAL, null);
  const optimizer = selectSixSlots(allocated, MODE_OPTIMIZER, null);
  assert.equal(normal.anchor.structure_id, "brand-new-anchor");
  assert.deepEqual(normal.leading.map((s) => s.structure_id), ["brand-new-stack"]);
  assert.deepEqual(optimizer.leading.map((s) => s.structure_id), ["brand-new-hybrid"]);
});

test("an unevaluated new project (no best_per_jurisdiction, no structures) never fabricates a scenario", () => {
  const allocated = { structures: [], ranking: [], best_per_jurisdiction: {} };
  const { slots, anchor, leading, slot6, dropdownOptions } = selectSixSlots(allocated, MODE_NORMAL, null);
  assert.equal(anchor, null);
  assert.deepEqual(leading, []);
  assert.equal(slot6, null);
  assert.deepEqual(slots, []);
  assert.deepEqual(dropdownOptions, []);
});

test("family constants are the exact canonical values, never inferred/renamed", () => {
  assert.deepEqual(NORMAL_FAMILIES, ["SINGLE_JURISDICTION", "STACKED_PROGRAMS"]);
  assert.deepEqual(OPTIMIZER_FAMILIES, [
    "HYBRID_ANCHOR_COMPONENT", "OFFICIAL_COPRODUCTION", "COMBINED_COPRO_HYBRID_STACK", "MULTI_PRINCIPAL_MULTILATERAL",
  ]);
});
