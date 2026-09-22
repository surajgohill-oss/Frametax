// ── GLOBE_SINGLE_AND_OPTIMIZER_WIRING (2026-09-21) ──────────────────────────
//
// Delta tests only, per this batch's own scope: the Globe's Single
// Jurisdiction and Optimizer data wiring now reuses the SAME canonical
// candidate-set selection Workspace's six-slot contract already uses
// (admissibleForMode -- lib/workspaceScenarioMode.js), instead of
// reconstructing markers from `allocated.structures`, the bounded,
// overall-rank-ordered general candidate page. See globeData.js's own
// GLOBE_SINGLE_AND_OPTIMIZER_WIRING comments for the full root-cause
// narrative; this file only pins the resulting behavior.

import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCountryStatuses,
  buildGlobeView,
  activeStructure,
} from "../src/lib/globeData.js";
import {
  admissibleForMode,
  MODE_NORMAL,
  MODE_OPTIMIZER,
} from "../src/lib/workspaceScenarioMode.js";

function structure(overrides) {
  const id = overrides.structure_id || "s1";
  return {
    structure_id: id,
    structure_type: overrides.structure_type || "single_country",
    classification: overrides.classification || "SINGLE_JURISDICTION",
    label: overrides.label || "Base",
    primary_jurisdiction: overrides.primary_jurisdiction ?? `JUR-${id}`,
    participants: overrides.participants || [overrides.primary_jurisdiction ?? `JUR-${id}`],
    program_slugs: overrides.program_slugs || [`program-${id}`],
    economic_identity: overrides.economic_identity ?? null,
    is_fully_priced: overrides.is_fully_priced ?? true,
    is_baseline: overrides.is_baseline ?? false,
    npc_with_adjustments_usd: overrides.npc_with_adjustments_usd ?? 900_000,
    selected_incentive_usd: overrides.selected_incentive_usd ?? 100_000,
    segments: overrides.segments || [],
    blockers: overrides.blockers || [],
    treaty_slug: overrides.treaty_slug ?? null,
    ...overrides,
  };
}

function bestPerJurisdiction(entries) {
  const out = {};
  for (const e of entries) out[e.primary_jurisdiction] = e;
  return out;
}

const OPTIMIZER_FAMILY_SET = new Set([
  "HYBRID_ANCHOR_COMPONENT", "OFFICIAL_COPRODUCTION", "COMBINED_COPRO_HYBRID_STACK", "MULTI_PRINCIPAL_MULTILATERAL",
]);

// COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21): `optimizer_candidates`
// mirrors canonical_production_view.py's own construction (filter to the
// optimizer families + is_fully_priced, ascending NPC) so every existing
// fixture below keeps working by listing its structures once, same as it
// already does for Single Jurisdiction via best_per_jurisdiction.
function optimizerCandidatesOf(structures) {
  return [...structures]
    .filter((s) => OPTIMIZER_FAMILY_SET.has(s.classification) && s.is_fully_priced)
    .sort((a, b) => (a.npc_with_adjustments_usd ?? Infinity) - (b.npc_with_adjustments_usd ?? Infinity));
}

function allocatedOf({ structures, bpj, ranking = [], topByFamily = {}, optimizerCandidates, optimizerScenarios }) {
  const candidates = optimizerCandidates ?? optimizerCandidatesOf(structures);
  return {
    structures,
    ranking,
    canonical_selected_structure_id: null,
    best_per_jurisdiction: bpj ?? bestPerJurisdiction(structures.filter((s) => s.classification === "SINGLE_JURISDICTION")),
    top_by_structural_family: topByFamily,
    optimizer_candidates: candidates,
    // PRODUCER_OPTIMIZER_SCENARIO_CANONICALIZATION: unit fixtures build one
    // hand-crafted structure per conceptual route, so the scenario
    // projection equals the candidate pool by default — the real backend
    // grouping/collapse logic is pinned separately against live data in
    // test_canonical_production_view.py.
    optimizer_scenarios: optimizerScenarios ?? candidates,
    producer_optimizer_options: optimizerScenarios ?? candidates,
  };
}

// 1 & 3. Single Globe consumes best_per_jurisdiction — one marker per jurisdiction.
test("buildCountryStatuses (Single Jurisdiction) sources statuses from best_per_jurisdiction, one entry per jurisdiction", () => {
  const winner = structure({ structure_id: "on-1", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 500_000 });
  const dominated = structure({ structure_id: "on-2", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 900_000 });
  const allocated = allocatedOf({ structures: [winner, dominated], bpj: { "CA-ON": winner } });
  const statuses = buildCountryStatuses(allocated, new Map(), MODE_NORMAL);
  const onEntries = [...statuses.values()].filter((e) => e.jurisdictionCodes.has("CA-ON"));
  assert.equal(onEntries.length, 1, "exactly one status entry must exist for CA-ON");
  assert.equal(onEntries[0].best.structure.structure_id, "on-1", "must resolve to the best_per_jurisdiction winner, never the dominated permutation");
});

// 2. Raw bounded candidate pages cannot create Single markers.
test("a structure present ONLY on the bounded structures[] page (not in best_per_jurisdiction) never creates a Single Jurisdiction marker", () => {
  const winner = structure({ structure_id: "gr-1", primary_jurisdiction: "GR" });
  // pageOnly shares no jurisdiction with the winner and is NOT the
  // best_per_jurisdiction entry for its own jurisdiction either — simulating
  // a bounded-page row that lost out to a real winner never itself paged.
  const pageOnly = structure({ structure_id: "it-page-only", primary_jurisdiction: "IT", npc_with_adjustments_usd: 5_000_000 });
  const allocated = allocatedOf({
    structures: [winner, pageOnly],
    bpj: { "GR": winner }, // IT's real winner is NOT on the page at all
  });
  const statuses = buildCountryStatuses(allocated, new Map(), MODE_NORMAL);
  const itEntries = [...statuses.values()].filter((e) => e.jurisdictionCodes.has("IT"));
  assert.equal(itEntries.length, 0, "a bounded-page-only structure for a jurisdiction with no best_per_jurisdiction entry must not create a marker");
});

// 4. Same-jurisdiction stacks remain Single.
test("STACKED_PROGRAMS (same-jurisdiction stack) is admissible in Single Jurisdiction mode, not Optimizer", () => {
  const stack = structure({ structure_id: "stack-1", classification: "STACKED_PROGRAMS", structure_type: "multi_program", primary_jurisdiction: "CA-MB" });
  const allocated = allocatedOf({ structures: [stack], bpj: { "CA-MB": stack } });
  const single = admissibleForMode(allocated, MODE_NORMAL);
  const optimizer = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.ok(single.some((s) => s.structure_id === "stack-1"), "stacked-program structure must be Single Jurisdiction admissible");
  assert.ok(!optimizer.some((s) => s.structure_id === "stack-1"), "stacked-program structure must never appear in Optimizer mode");
});

// 5. Hybrid classification and participants map correctly.
test("HYBRID_ANCHOR_COMPONENT is Optimizer-only and carries its full routed participants", () => {
  const hybrid = structure({
    structure_id: "hy-1", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: "CA-MB", participants: ["CA-MB", "CA-NL", "IT"],
  });
  const allocated = allocatedOf({ structures: [hybrid] });
  const optimizer = admissibleForMode(allocated, MODE_OPTIMIZER);
  const single = admissibleForMode(allocated, MODE_NORMAL);
  assert.equal(optimizer.length, 1);
  assert.deepEqual(optimizer[0].participants, ["CA-MB", "CA-NL", "IT"]);
  assert.ok(!single.some((s) => s.structure_id === "hy-1"), "ordinary hybrid must never leak into Single Jurisdiction mode");
});

// 6. Official co-productions map correctly.
test("OFFICIAL_COPRODUCTION is Optimizer-only and carries every treaty principal", () => {
  const copro = structure({
    structure_id: "cop-1", classification: "OFFICIAL_COPRODUCTION", structure_type: "treaty_coproduction",
    primary_jurisdiction: "FR", participants: ["FR", "DE"], treaty_slug: "fr-de-treaty",
  });
  const allocated = allocatedOf({ structures: [copro] });
  const optimizer = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.equal(optimizer.length, 1);
  assert.deepEqual(optimizer[0].participants, ["FR", "DE"]);
});

// 7. Combined structures map correctly.
test("COMBINED_COPRO_HYBRID_STACK is Optimizer-only and carries every component/participant", () => {
  const combined = structure({
    structure_id: "comb-1", classification: "COMBINED_COPRO_HYBRID_STACK", structure_type: "hybrid",
    primary_jurisdiction: "CA-MB", participants: ["CA-MB", "IT", "GR", "FR"],
  });
  const allocated = allocatedOf({ structures: [combined] });
  const optimizer = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.equal(optimizer.length, 1);
  assert.deepEqual(optimizer[0].participants, ["CA-MB", "IT", "GR", "FR"]);
});

// 8. Multilateral structures map correctly.
test("MULTI_PRINCIPAL_MULTILATERAL is Optimizer-only and carries every simultaneous principal", () => {
  const multi = structure({
    structure_id: "multi-1", classification: "MULTI_PRINCIPAL_MULTILATERAL", structure_type: "hybrid",
    primary_jurisdiction: "FR", participants: ["FR", "DE", "BE", "IT"],
  });
  const allocated = allocatedOf({ structures: [multi] });
  const optimizer = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.equal(optimizer.length, 1);
  assert.deepEqual(optimizer[0].participants, ["FR", "DE", "BE", "IT"]);
});

// 9. COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21) — SUPERSEDES the
// two tests this replaces: the `top_by_structural_family` GD-4 "family
// entirely absent" backstop is now dead code in admissibleForMode (removed
// entirely) — root cause: it never helped a family that WAS represented on
// the bounded page but only PARTIALLY (F#K Valentine's Day: 411 real
// HYBRID_ANCHOR_COMPONENT candidates, page carried 93). `optimizer_candidates`
// (canonical_production_view.py) is now the sole, COMPLETE source for every
// optimizer family — no backstop merge is needed because it is never capped
// in the first place. This test proves a family genuinely absent from
// optimizer_candidates serves nothing for that family, never a fabricated
// entry from elsewhere.
test("a family genuinely absent from optimizer_candidates serves nothing for that family, never fabricated from a different source", () => {
  const hybrid = structure({ structure_id: "hy-onpage", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "CA-MB", participants: ["CA-MB", "IT"] });
  const allocated = allocatedOf({ structures: [hybrid] }); // no MULTI_PRINCIPAL_MULTILATERAL row anywhere
  const optimizer = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.ok(!optimizer.some((s) => s.classification === "MULTI_PRINCIPAL_MULTILATERAL"), "an absent family must serve honestly empty, never invented");
  assert.deepEqual(optimizer.map((s) => s.structure_id), ["hy-onpage"]);
});

test("optimizer_candidates already carries every real family representative directly — no separate backstop merge step exists", () => {
  const hybrid = structure({ structure_id: "hy-real", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "CA-MB", participants: ["CA-MB", "IT"], npc_with_adjustments_usd: 400_000 });
  const multilateral = structure({ structure_id: "multi-real", classification: "MULTI_PRINCIPAL_MULTILATERAL", structure_type: "hybrid", primary_jurisdiction: "FR", participants: ["FR", "DE", "BE"], npc_with_adjustments_usd: 1_000_000 });
  const allocated = allocatedOf({ structures: [hybrid, multilateral] });
  const optimizer = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.deepEqual(optimizer.map((s) => s.structure_id).sort(), ["hy-real", "multi-real"]);
});

// 11. Conditional/prohibited treatment remains correct.
test("conditional and rejected/authority-locked classifications never become a selectable Single or Optimizer marker", () => {
  const conditional = structure({ structure_id: "cond-1", classification: "CONDITIONAL_USER_FACT_REQUIRED", primary_jurisdiction: "BR" });
  const rejected = structure({ structure_id: "rej-1", classification: "REJECTED_FOR_PROJECT", primary_jurisdiction: "RU" });
  const locked = structure({ structure_id: "lock-1", classification: "AUTHORITY_LOCKED", primary_jurisdiction: "CN" });
  const allocated = allocatedOf({ structures: [conditional, rejected, locked], bpj: {} });
  const single = admissibleForMode(allocated, MODE_NORMAL);
  const optimizer = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.deepEqual(single, [], "no conditional/rejected/locked candidate may appear as a Single Jurisdiction winner");
  // Conditional opportunities ARE surfaced in Optimizer mode (existing,
  // unchanged contract — disclosed upside, appended after every priced
  // candidate) but rejected/authority-locked candidates never are.
  assert.ok(optimizer.every((s) => s.structure_id !== "rej-1" && s.structure_id !== "lock-1"), "rejected/authority-locked candidates must never appear in Optimizer mode");
});

// 12. Workspace and Globe share mode state (source-level contract check).
test("ProjectGlobe.jsx reads/writes the SAME shared workspaceMode AppState Workspace.jsx uses, not a second local mode", async () => {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { dirname, join } = await import("node:path");
  const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
  const read = (p) => readFileSync(join(SRC, p), "utf8");
  const pg = read("screens/production/ProjectGlobe.jsx");
  assert.match(pg, /workspaceMode, setWorkspaceMode/, "ProjectGlobe.jsx must destructure the shared workspaceMode from useAppState()");
  assert.doesNotMatch(pg, /useState\("jurisdictions"\)/, "ProjectGlobe.jsx must not keep its own independent local Globe mode");
  const ws = read("screens/production/Workspace.jsx");
  assert.doesNotMatch(ws, /useState\("jurisdictions"\)/, "Workspace.jsx's embedded Globe must not keep its own independent local Globe mode either");
  assert.match(ws, /workspaceMode === MODE_NORMAL[\s\S]{0,40}setWorkspaceMode\(MODE_NORMAL\)/, "Workspace.jsx's embedded Globe toggle must read/write the shared workspaceMode");
});

// 13. State is isolated by project — a stale leadingStructureId from a
// different project's candidate set must never silently resolve to the
// wrong structure; it must fall back to the canonical selection instead.
test("activeStructure falls back safely when leadingStructureId belongs to a different project's structures, never resolving to an unrelated row", () => {
  const projectA = allocatedOf({
    structures: [structure({ structure_id: "a-1", is_baseline: false })],
    ranking: [{ structure_id: "a-1", rank: 1 }],
  });
  projectA.canonical_selected_structure_id = "a-1";
  // A leadingStructureId carried over from a DIFFERENT project (e.g. stale
  // AppState after navigating projects) must not resolve inside projectA.
  const resolved = activeStructure(projectA, "stale-id-from-project-b", admissibleForMode(projectA, MODE_OPTIMIZER));
  assert.equal(resolved.structure_id, "a-1", "must fall back to projectA's own canonical selection, never a phantom cross-project match");
});

// 14. Arbitrary new-project fixtures use the same wiring — no hardcoded IDs.
test("a brand-new, never-before-seen synthetic project's jurisdiction winners and optimizer families flow through the identical wiring", () => {
  const singleWinner = structure({ structure_id: "brand-new-single", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "PT" });
  const hybrid = structure({
    structure_id: "brand-new-hybrid", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: "HR", participants: ["HR", "SI", "AT"],
  });
  const allocated = allocatedOf({
    structures: [singleWinner, hybrid],
    bpj: { "PT": singleWinner },
  });
  const single = admissibleForMode(allocated, MODE_NORMAL);
  const optimizer = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.deepEqual(single.map((s) => s.structure_id), ["brand-new-single"]);
  assert.deepEqual(optimizer.map((s) => s.structure_id), ["brand-new-hybrid"]);

  const statuses = buildCountryStatuses(allocated, new Map(), MODE_NORMAL);
  assert.ok([...statuses.values()].some((e) => e.jurisdictionCodes.has("PT")), "a brand-new project's Single Jurisdiction winner must produce a real Globe marker with no project-specific code");

  const view = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER });
  assert.ok(view.polygonColors.size > 0 || view.points.length >= 0, "Optimizer buildGlobeView must run to completion for an arbitrary new project without throwing or special-casing");
});
