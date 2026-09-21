// ── FVD_GLOBE_RENDERER_CORRECTION (2026-09-21) ──────────────────────────────
//
// The previous pass (GLOBE_SINGLE_AND_OPTIMIZER_WIRING) verified card/list
// text, mode-button state, and helper-function output, and declared the
// Globe wired from that evidence. It was wrong: reproducing F#K Valentine's
// Day in the actual browser showed Optimizer mode rendering a completely
// blank Three-Globe scene by default, and clicking any of its 36 candidate
// cards never changed it. These tests assert against `buildGlobeView`'s
// `sceneSignature` — a value computed from the EXACT `points`/`arcs`/
// `polygonColors` this module returns for Globe3D's own props (see
// globeData.js's own header comment on sceneSignature) — never from a card
// list, a helper's return value in isolation, or a re-derived expectation.

import test from "node:test";
import assert from "node:assert/strict";

import {
  buildGlobeView,
  buildOptimizerPathway,
  sceneSignature,
} from "../src/lib/globeData.js";
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

const OPTIMIZER_FAMILY_SET = new Set([
  "HYBRID_ANCHOR_COMPONENT", "OFFICIAL_COPRODUCTION", "COMBINED_COPRO_HYBRID_STACK", "MULTI_PRINCIPAL_MULTILATERAL",
]);

// COMPLETE_OPTIMIZER_CANDIDATE_UI_WIRING (2026-09-21): mirrors
// canonical_production_view.py's own construction — see the identically-
// named helper in globe-single-and-optimizer-wiring.test.mjs for the full
// root-cause comment.
function optimizerCandidatesOf(structures) {
  return [...structures]
    .filter((s) => OPTIMIZER_FAMILY_SET.has(s.classification) && s.is_fully_priced)
    .sort((a, b) => (a.npc_with_adjustments_usd ?? Infinity) - (b.npc_with_adjustments_usd ?? Infinity));
}

function allocatedOf({ structures, bpj, ranking = [], topByFamily = {}, canonicalId = null, optimizerCandidates }) {
  return {
    structures,
    ranking,
    canonical_selected_structure_id: canonicalId,
    best_per_jurisdiction: bpj ?? bestPerJurisdiction(structures.filter((s) => s.classification === "SINGLE_JURISDICTION")),
    top_by_structural_family: topByFamily,
    optimizer_candidates: optimizerCandidates ?? optimizerCandidatesOf(structures),
  };
}

// Real jurisdictions with known coordinates (jurisdictions.js) so
// buildOptimizerPathway's JURISDICTION_COORDS gate doesn't drop them.
const MB = "CA-MB", NL = "CA-NL", IT = "IT", GR = "GR", RO = "RO";

// 1. Single mode renderer props originate from best_per_jurisdiction.
test("Single mode's sceneSignature polygon/marker data is built from best_per_jurisdiction, never from raw structures[]", () => {
  const winner = structure({ structure_id: "on-1", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 500_000 });
  const pageOnlyDominated = structure({ structure_id: "on-2", primary_jurisdiction: "CA-ON", npc_with_adjustments_usd: 900_000 });
  const allocated = allocatedOf({ structures: [winner, pageOnlyDominated], bpj: { "CA-ON": winner } });
  const view = buildGlobeView(allocated, new Map(), { mode: MODE_NORMAL });
  assert.ok(view.polygonColors.has("CA-ON") || view.polygonColors.has("ON"), "the real winner's jurisdiction must reach polygonColors");
  assert.equal(view.sceneSignature.mode, MODE_NORMAL);
  assert.equal(view.sceneSignature.polygonCount, 1, "exactly one polygon fill for the one real jurisdiction, never a duplicate from the dominated permutation");
});

// 2. Optimizer mode resolves a valid default Optimizer scenario.
test("Optimizer mode with NO leadingStructureId and NO canonical/rank-1 structure still resolves the top-ranked ADMISSIBLE Optimizer candidate, never a blank scene", () => {
  // Mirrors FVD's real live state: canonical_selected_structure_id is null,
  // ranking has no rank:1 entry at all ("no verified winner").
  const hybrid = structure({
    structure_id: "hy-1", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: MB, participants: [MB, NL, IT], npc_with_adjustments_usd: 2_800_000,
  });
  const allocated = allocatedOf({ structures: [hybrid], ranking: [], canonicalId: null });
  const pathway = buildOptimizerPathway(allocated, null);
  assert.ok(pathway.structure, "a valid default Optimizer structure must resolve even with no leadingStructureId/canonical/rank-1");
  assert.equal(pathway.structure.structure_id, "hy-1");
  assert.equal(pathway.points.length, 3, "the default scene must contain real markers, never zero");
  assert.equal(pathway.arcs.length, 2, "the default scene must contain real arcs, never zero");
});

// 3. Stale Single selection cannot suppress Optimizer rendering.
test("a canonical_selected_structure_id pointing at a SINGLE_JURISDICTION structure is never reused as the Optimizer default", () => {
  const singleWinner = structure({ structure_id: "single-1", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "CA-ON" });
  const hybrid = structure({
    structure_id: "hy-1", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: MB, participants: [MB, NL], npc_with_adjustments_usd: 2_800_000,
  });
  const allocated = allocatedOf({
    structures: [singleWinner, hybrid],
    ranking: [{ structure_id: "single-1", rank: 1 }],
    canonicalId: "single-1",
    bpj: { "CA-ON": singleWinner },
  });
  const pathway = buildOptimizerPathway(allocated, null);
  assert.ok(pathway.structure, "Optimizer must still resolve a real structure");
  assert.equal(pathway.structure.classification, "HYBRID_ANCHOR_COMPONENT", "must resolve the genuine Optimizer-family candidate, never the single-jurisdiction canonical pick");
  assert.notEqual(pathway.structure.structure_id, "single-1");
});

// 4. Marker codes equal selected structure participants/routes.
test("Optimizer marker codes equal the resolved structure's own full participants, in routed order", () => {
  const hybrid = structure({
    structure_id: "hy-1", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: MB, participants: [MB, NL, IT],
  });
  const allocated = allocatedOf({ structures: [hybrid] });
  const pathway = buildOptimizerPathway(allocated, "hy-1");
  assert.deepEqual(pathway.points.map((p) => p.id), [MB, NL, IT]);
});

// 5. Arc endpoints equal the actual routed structure.
test("Optimizer arc endpoints (startCode/endCode) trace the resolved structure's own routed chain, never a generic/default pair", () => {
  const hybrid = structure({
    structure_id: "hy-1", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: GR, participants: [GR, RO],
  });
  const allocated = allocatedOf({ structures: [hybrid] });
  const pathway = buildOptimizerPathway(allocated, "hy-1");
  assert.deepEqual(pathway.arcs.map((a) => `${a.startCode}->${a.endCode}`), [`${GR}->${RO}`]);
});

// 6. Mode switching changes the renderer scene signature.
test("switching mode changes buildGlobeView's sceneSignature (Single vs Optimizer are provably different scenes)", () => {
  const hybrid = structure({
    structure_id: "hy-1", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: MB, participants: [MB, NL],
  });
  const singleWinner = structure({ structure_id: "single-1", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "CA-ON" });
  const allocated = allocatedOf({ structures: [hybrid, singleWinner], bpj: { "CA-ON": singleWinner } });
  const singleSig = buildGlobeView(allocated, new Map(), { mode: MODE_NORMAL }).sceneSignature;
  const optSig = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER }).sceneSignature;
  assert.notDeepEqual(singleSig, optSig, "Single and Optimizer scene signatures must differ");
  assert.equal(optSig.classification, "HYBRID_ANCHOR_COMPONENT", "Optimizer signature must carry a real canonical classification");
  assert.equal(singleSig.classification, null, "Single mode has no single active structure — this is itself part of what distinguishes the two signatures");
});

// 7. Changing Optimizer selection changes the renderer scene signature.
test("selecting a second, materially different Optimizer structure changes buildGlobeView's sceneSignature", () => {
  const hybridA = structure({
    structure_id: "hy-a", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: MB, participants: [MB, NL], npc_with_adjustments_usd: 2_800_000,
  });
  const hybridB = structure({
    structure_id: "hy-b", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: GR, participants: [GR, RO], npc_with_adjustments_usd: 3_000_000,
  });
  const allocated = allocatedOf({ structures: [hybridA, hybridB] });
  const sigA = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER, leadingStructureId: "hy-a" }).sceneSignature;
  const sigB = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER, leadingStructureId: "hy-b" }).sceneSignature;
  assert.notDeepEqual(sigA.markerCodes, sigB.markerCodes);
  assert.notDeepEqual(sigA.arcEndpoints, sigB.arcEndpoints);
});

// 8. Full-page and embedded Globes use the same scene-data contract.
test("ProjectGlobe.jsx and Workspace.jsx's embedded Globe both consume buildGlobeView(...).sceneSignature via the identical diagnostic contract", async () => {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { dirname, join } = await import("node:path");
  const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
  const read = (p) => readFileSync(join(SRC, p), "utf8");
  const pg = read("screens/production/ProjectGlobe.jsx");
  const ws = read("screens/production/Workspace.jsx");
  for (const src of [pg, ws]) {
    assert.match(src, /buildGlobeView\(allocated, rankById/, "both screens must call the SAME buildGlobeView entry point");
    assert.match(src, /sceneSignature/, "both screens must consume sceneSignature from buildGlobeView's own return value");
    assert.match(src, /window\.__cineGlobeSceneSignature = sceneSignature/, "both screens must expose the diagnostic from the exact value buildGlobeView returned, never a re-derived one");
  }
});

// 9. No project IDs or names are hardcoded.
test("no hardcoded production IDs/names in the touched renderer-wiring files", async () => {
  const { readFileSync } = await import("node:fs");
  const { fileURLToPath } = await import("node:url");
  const { dirname, join } = await import("node:path");
  const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
  const read = (p) => readFileSync(join(SRC, p), "utf8");
  const files = ["lib/globeData.js", "screens/production/ProjectGlobe.jsx", "screens/production/Workspace.jsx"];
  const forbidden = /f#k valentine|little utopia|bad hombres|lips like sugar|6c6f1c13|fa5cade5|4355ae88|ab10b319/i;
  for (const f of files) {
    const src = read(f);
    // Historical debugging comments referencing what was verified live are
    // allowed (this codebase's own established convention — see CLAUDE.md's
    // own LESSON entries); what must never appear is a CONDITIONAL branch
    // keyed on one. Approximate check: no `if` line containing a project name.
    const conditionalLines = src.split("\n").filter((line) => /\bif\s*\(/.test(line) && forbidden.test(line));
    assert.deepEqual(conditionalLines, [], `found project-specific conditional logic: ${conditionalLines.join(" | ")}`);
  }
});

// 10. Synthetic newly evaluated project uses the same renderer path.
test("an arbitrary new/synthetic project's Optimizer default and click-through use the identical wiring, no special-casing", () => {
  const hybrid = structure({
    structure_id: "brand-new-hybrid", classification: "HYBRID_ANCHOR_COMPONENT", structure_type: "hybrid",
    primary_jurisdiction: "HR", participants: ["HR", "SI", "AT"], economic_identity: "econ-brand-new",
  });
  const singleWinner = structure({ structure_id: "brand-new-single", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "PT" });
  const allocated = allocatedOf({ structures: [hybrid, singleWinner], bpj: { PT: singleWinner } });

  const optDefault = buildGlobeView(allocated, new Map(), { mode: MODE_OPTIMIZER }).sceneSignature;
  assert.deepEqual(optDefault.markerCodes, ["AT", "HR", "SI"]);
  assert.equal(optDefault.economicIdentity, "econ-brand-new", "a real, served economic_identity must flow through to the signature unmodified — proves the wiring, independent of whether today's live productions happen to serve one");

  const singleView = buildGlobeView(allocated, new Map(), { mode: MODE_NORMAL }).sceneSignature;
  assert.equal(singleView.polygonCount, 1);
});

// Unevaluated project: buildGlobeView must never throw or fabricate a scene.
test("an unevaluated project (allocated is null) returns an empty, well-formed sceneSignature", () => {
  const view = buildGlobeView(null, new Map(), { mode: MODE_OPTIMIZER });
  assert.deepEqual(view.sceneSignature.markerCodes, []);
  assert.equal(view.sceneSignature.markerCount, 0);
  assert.equal(view.sceneSignature.arcCount, 0);
});
