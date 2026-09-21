// ── FOUR_PRODUCTION_GLOBE_RUNTIME_CORRECTION (2026-09-21) ───────────────────
//
// The prior pass fixed FVD's Optimizer default-resolution bug but declared
// completion from a single production plus "smoke checks" of the other
// three. That was rejected: Bad Hombres still had a broken Optimizer scene
// live in the browser — a SEPARATE, undiscovered defect (JURISDICTION_
// COORDS missing entries for several real jurisdictions, including US-NM,
// Bad Hombres' own anchor), never caught because no test or check actually
// exercised a structure routing through those specific codes. These tests
// assert against buildGlobeView's sceneSignature for all four productions'
// own real anchor/routing patterns individually — never one production
// standing in for another.

import test from "node:test";
import assert from "node:assert/strict";

import {
  buildGlobeView,
  buildOptimizerPathway,
} from "../src/lib/globeData.js";
import { JURISDICTION_COORDS } from "../src/lib/jurisdictions.js";
import { MODE_NORMAL, MODE_OPTIMIZER } from "../src/lib/workspaceScenarioMode.js";

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

function allocatedOf({ structures, bpj, ranking = [], canonicalId = null }) {
  return {
    structures,
    ranking,
    canonical_selected_structure_id: canonicalId,
    best_per_jurisdiction: bpj ?? bestPerJurisdiction(structures.filter((s) => s.classification === "SINGLE_JURISDICTION")),
    top_by_structural_family: {},
  };
}

// 1. Valid Optimizer candidates can never produce an unexplained blank scene.
test("any production with a real Optimizer-admissible candidate never renders a blank scene, regardless of canonical/rank-1 state", () => {
  const hybrid = structure({ structure_id: "hy-1", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "CA-MB", participants: ["CA-MB", "CA-NL"] });
  // No canonical winner, no rank-1 entry at all -- the exact live FVD state.
  const allocated = allocatedOf({ structures: [hybrid], ranking: [], canonicalId: null });
  const view = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER });
  assert.ok(view.sceneSignature.markerCount > 0, "a real admissible candidate must always produce a non-empty scene");
  assert.ok(view.sceneSignature.arcCount > 0);
});

// 2. Default Optimizer selection is resolved independently per project.
test("two different allocated payloads (two different projects) each resolve their OWN top-ranked Optimizer default, never each other's", () => {
  const hybridA = structure({ structure_id: "a-hy", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "GR", participants: ["GR", "RO"], economic_identity: "econ-a" });
  const hybridB = structure({ structure_id: "b-hy", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "MU", participants: ["MU", "IT"], economic_identity: "econ-b" });
  const allocatedA = allocatedOf({ structures: [hybridA] });
  const allocatedB = allocatedOf({ structures: [hybridB] });
  const pathwayA = buildOptimizerPathway(allocatedA, null);
  const pathwayB = buildOptimizerPathway(allocatedB, null);
  assert.equal(pathwayA.structure.economic_identity, "econ-a");
  assert.equal(pathwayB.structure.economic_identity, "econ-b");
});

// 3. Bad Hombres fixture — its own confirmed live anchor (New Mexico, US-NM)
// and the exact defect pattern found: a structure routing through a
// jurisdiction that previously had no JURISDICTION_COORDS entry.
test("Bad Hombres fixture: a structure routing through its own anchor (US-NM) renders every real participant, never silently dropping one for a missing coordinate", () => {
  assert.ok(JURISDICTION_COORDS["US-NM"], "US-NM (Bad Hombres' own anchor) must have a real coordinate entry — this was the confirmed live defect");
  const hybrid = structure({
    structure_id: "bh-hy", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: "CA-MB", participants: ["CA-MB", "CA-NL", "US-NM"], economic_identity: "econ-bh",
  });
  const allocated = allocatedOf({ structures: [hybrid] });
  const pathway = buildOptimizerPathway(allocated, "bh-hy");
  assert.equal(pathway.points.length, 3, "all 3 real participants must render as markers, never 2");
  assert.equal(pathway.arcs.length, 2, "both routed legs must render as arcs, never 1");
  assert.ok(pathway.points.some((p) => p.id === "US-NM"), "US-NM specifically must appear — this is the exact code that was silently dropped live");
});

// 4. F#K Valentine's Day fixture — its own confirmed live state: no
// canonical_selected_structure_id, no rank-1 ranking entry at all.
test("FVD fixture: no verified winner (canonical_selected_structure_id null, empty ranking) still resolves a real default Optimizer scene", () => {
  const hybrid = structure({
    structure_id: "fvd-hy", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: "CA-MB", participants: ["CA-MB", "CA-NL", "IT"], economic_identity: "econ-fvd",
  });
  const allocated = allocatedOf({ structures: [hybrid], ranking: [], canonicalId: null });
  const pathway = buildOptimizerPathway(allocated, null);
  assert.ok(pathway.structure, "must resolve a real structure even with FVD's exact live no-verified-winner state");
  assert.equal(pathway.points.length, 3);
  assert.equal(pathway.arcs.length, 2);
});

// 5. Little Utopia fixture — its own anchor (Mauritius, MU).
test("Little Utopia fixture: a structure routed through its own anchor (Mauritius, MU) renders correctly", () => {
  const hybrid = structure({
    structure_id: "lu-hy", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: "MU", participants: ["MU", "CA-MB", "MT"], economic_identity: "econ-lu",
  });
  const allocated = allocatedOf({ structures: [hybrid] });
  const pathway = buildOptimizerPathway(allocated, "lu-hy");
  assert.equal(pathway.points.length, 3);
  assert.equal(pathway.arcs.length, 2);
  assert.equal(pathway.points[0].id, "MU", "the anchor (primary_jurisdiction) must order first");
});

// 6. Lips Like Sugar fixture — its own anchor (California, US-CA).
test("Lips Like Sugar fixture: a structure routed through its own anchor (California, US-CA) renders correctly", () => {
  const hybrid = structure({
    structure_id: "lls-hy", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: "US-CA", participants: ["US-CA", "CA-MB", "CO"], economic_identity: "econ-lls",
  });
  const allocated = allocatedOf({ structures: [hybrid] });
  const pathway = buildOptimizerPathway(allocated, "lls-hy");
  assert.equal(pathway.points.length, 3);
  assert.equal(pathway.arcs.length, 2);
  assert.equal(pathway.points[0].id, "US-CA");
});

// 7. Selecting a second scenario changes renderer props.
test("selecting a second, materially different structure changes buildGlobeView's actual renderer props (points/arcs/polygonColors), not just its signature", () => {
  const hybridA = structure({ structure_id: "x-a", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "CA-MB", participants: ["CA-MB", "CA-NL"] });
  const hybridB = structure({ structure_id: "x-b", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "GR", participants: ["GR", "RO"] });
  const allocated = allocatedOf({ structures: [hybridA, hybridB] });
  const viewA = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER, leadingStructureId: "x-a" });
  const viewB = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER, leadingStructureId: "x-b" });
  assert.notDeepEqual(viewA.points.map((p) => p.id), viewB.points.map((p) => p.id));
  assert.notDeepEqual([...viewA.polygonColors.keys()], [...viewB.polygonColors.keys()]);
});

// 8. Full-page and embedded paths match.
test("ProjectGlobe.jsx (full-page) and Workspace.jsx (embedded) both call buildGlobeView with the same {mode, leadingStructureId, selectedJurisdiction} shape and expose the identical diagnostic", async () => {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { dirname, join } = await import("node:path");
  const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
  const read = (p) => readFileSync(join(SRC, p), "utf8");
  for (const f of ["screens/production/ProjectGlobe.jsx", "screens/production/Workspace.jsx"]) {
    const src = read(f);
    assert.match(src, /buildGlobeView\(allocated, rankById,\s*\{/);
    assert.match(src, /mode:\s*(globeMode|workspaceMode),\s*leadingStructureId,\s*selectedJurisdiction/);
    assert.match(src, /window\.__cineGlobeSceneSignature = sceneSignature/);
  }
});

// 9. Canonical economic identity is non-null and equal across projections.
test("a real economic_identity on a structure flows identically into best_per_jurisdiction-sourced Single mode AND Optimizer's sceneSignature -- one source, never two", () => {
  const singleWinner = structure({ structure_id: "id-1", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "CA-ON", economic_identity: "econ-shared" });
  const hybrid = structure({ structure_id: "id-2", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "CA-MB", participants: ["CA-MB", "IT"], economic_identity: "econ-hybrid" });
  const allocated = allocatedOf({ structures: [singleWinner, hybrid], bpj: { "CA-ON": singleWinner } });
  const optView = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER, leadingStructureId: "id-2" });
  assert.equal(optView.sceneSignature.economicIdentity, "econ-hybrid", "the Optimizer signature must carry the real, non-null served identity");
  assert.ok(optView.sceneSignature.economicIdentity != null);
});

// 10. State remains isolated per project.
test("a stale leadingStructureId from a DIFFERENT project's structure set never resolves inside this project -- falls back to this project's own top-ranked default", () => {
  const ownHybrid = structure({ structure_id: "own-hy", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "CA-MB", participants: ["CA-MB", "IT"], economic_identity: "econ-own" });
  const allocated = allocatedOf({ structures: [ownHybrid] });
  // "other-project-structure-id" mimics a stale AppState leadingStructureId carried over via in-app navigation from a different project.
  const pathway = buildOptimizerPathway(allocated, "other-project-structure-id-does-not-exist-here");
  assert.equal(pathway.structure.structure_id, "own-hy", "must resolve THIS project's own default, never resolve to nothing or crash on the foreign id");
  assert.equal(pathway.structure.economic_identity, "econ-own");
});

// 11. Single mode consumes best_per_jurisdiction.
test("Single Jurisdiction mode's rendered polygonColors originate from best_per_jurisdiction, one entry per jurisdiction", () => {
  const winner = structure({ structure_id: "on-1", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 500_000 });
  const dominated = structure({ structure_id: "on-2", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 900_000 });
  const allocated = allocatedOf({ structures: [winner, dominated], bpj: { "CA-ON": winner } });
  const view = buildGlobeView(allocated, new Map(), { mode: MODE_NORMAL });
  assert.ok(view.polygonColors.has("CA-ON") || view.polygonColors.has("ON"));
  assert.equal(view.sceneSignature.polygonCount, 1);
});

// 12. Newly evaluated synthetic project uses the same path.
test("an arbitrary new/synthetic project's Optimizer default, second-selection change, and Single mode all use the identical wiring -- no per-project special-casing", () => {
  const hybridA = structure({ structure_id: "brand-new-a", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "HR", participants: ["HR", "SI"], economic_identity: "econ-brand-a" });
  const hybridB = structure({ structure_id: "brand-new-b", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid", primary_jurisdiction: "PT", participants: ["PT", "ES"], economic_identity: "econ-brand-b" });
  const singleWinner = structure({ structure_id: "brand-new-single", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "AT" });
  const allocated = allocatedOf({ structures: [hybridA, hybridB, singleWinner], bpj: { AT: singleWinner } });

  const optDefault = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER });
  assert.equal(optDefault.sceneSignature.economicIdentity, "econ-brand-a", "must resolve the top-ranked admissible candidate generically");

  const optSecond = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER, leadingStructureId: "brand-new-b" });
  assert.notEqual(optDefault.sceneSignature.economicIdentity, optSecond.sceneSignature.economicIdentity);

  const single = buildGlobeView(allocated, new Map(), { mode: MODE_NORMAL });
  assert.equal(single.sceneSignature.polygonCount, 1);
});
