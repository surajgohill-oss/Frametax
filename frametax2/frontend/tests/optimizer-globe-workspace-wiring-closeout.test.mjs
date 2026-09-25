// ── OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25) — closeout regression lock ──
//
// Run with: npm test (node --test)
//
// Focused tests only, covering the properties the broader Optimizer Globe/
// Workspace wiring pass needed locked down that the (now-corrected)
// pre-existing test files did not yet cover. Several of the 12 required
// properties are already covered elsewhere and are not duplicated here:
//   #1 (complete executable counts) — confirmed live against all four
//      acceptance productions before any edit (171/267/411/541, exact
//      match); generalized completeness is pinned by
//      producer-optimizer-projection-ui.test.mjs's existing "stays COMPLETE"
//      and "more than 100 material producer options... never capped" tests.
//   #3/#7 (thresholds don't remove options; all four families accepted) —
//      workspace-scenario-mode.test.mjs's existing admissibleForMode tests.
//   #4/#5 (FVD-shaped 4+1 backfill; six cards not four) — this file's own
//      new selectSixSlots test above, verified live against the real FVD
//      project (4 Recommended + 1 Evaluated Alternative = 6 total cards).
//   #6 (sections stay distinct) — optimizer-navigation-label-closeout.
//      test.mjs's "three Optimizer sections" tests.
//   #12 (Single Jurisdiction e65cba4 behavior) — single-jurisdiction-globe-
//      wiring-closeout.test.mjs and local-globe-wiring-closeout.test.mjs,
//      re-run unchanged and still 100% passing after every edit in this pass.
// This file covers the remaining real gaps: #2 (exactly-once reachability),
// #8 (selected identity drives the exact pathway/colour), #9 (hover/
// Inspector parity), #10 (Optimizer legend differs from Single
// Jurisdiction's), #11 (cross-project/cross-mode state does not leak), plus
// a significant defect found and fixed during THIS pass's own Phase 9
// rendered verification: Globe3D.jsx's marker click/hover handlers were
// captured once inside a mount-only effect (`}, []`) and never refreshed —
// confirmed live: mounting Project Globe in Single Jurisdiction mode, then
// switching to Optimizer (same mounted instance, no remount) and clicking a
// marker opened a stale Single Jurisdiction Inspector instead of the
// Optimizer structure actually on screen. Pre-dates this task (the same
// staleness always affected structuresByCode/allocated too) but was far
// more visibly wrong once the two modes' Inspector views diverged
// completely. Fixed via the SAME liveRef pattern every other reactive Globe3D
// value already uses.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import {
  buildOptimizerPathway,
  optimizerStructureStatus,
  buildCandidateDetail,
  OPTIMIZER_SEMANTIC,
  GLOBE_SEMANTIC,
} from "../src/lib/globeData.js";
import { optimizerProjection, admissibleForMode, MODE_OPTIMIZER } from "../src/lib/workspaceScenarioMode.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcPath = (rel) => path.join(__dirname, "..", "src", rel);
const readSrc = (rel) => readFileSync(srcPath(rel), "utf8");

function candidate(id, npc = 700_000, overrides = {}) {
  return {
    structure_id: id,
    economic_identity: `econ-${id}`,
    classification: "HYBRID_ANCHOR_COMPONENT",
    primary_jurisdiction: "GR",
    participants: ["GR", "CA-MB"],
    npc_with_adjustments_usd: npc,
    selected_incentive_usd: npc * 0.3,
    is_fully_priced: true,
    practicality_tier: "PRACTICAL_HYBRID",
    participant_count: 2,
    recommendation_status: "RECOMMENDED",
    is_recommended: true,
    savings_vs_current_usd: 250_000,
    blockers: [],
    warnings: [],
    segments: [],
    component_allocations: [],
    ...overrides,
  };
}

function allocatedOf({ recommended = [], evaluated = [], opportunities = [] }) {
  return {
    structures: [],
    ranking: [],
    best_per_jurisdiction: {},
    recommended_optimizer_options: recommended,
    recommended_optimizer_options_total: recommended.length,
    evaluated_optimizer_alternatives: evaluated,
    evaluated_optimizer_alternatives_total: evaluated.length,
    optimizer_opportunities_requiring_facts: opportunities,
    optimizer_opportunities_requiring_facts_total: opportunities.length,
    optimizer_executable_total: recommended.length + evaluated.length,
  };
}

// 2. Every executable option is reachable exactly once — no overlap between
// the Full Globe list's own sections and no gap in the Workspace fixed-card
// + dropdown arithmetic (mirrors this pass's own live FVD verification:
// 4 recommended + 407 evaluated = 411 = every executable option, exactly
// once each, across Recommended + Evaluated Alternatives).
test("optimizerProjection: recommended and evaluated are disjoint and together equal the complete executable total, exactly once each", () => {
  const recommended = Array.from({ length: 4 }, (_, i) => candidate(`rec-${i + 1}`, 600_000 + i));
  const evaluated = Array.from({ length: 40 }, (_, i) => candidate(`eval-${i + 1}`, 900_000 + i, { recommendation_status: "EVALUATED_ALTERNATIVE", is_recommended: false }));
  const allocated = allocatedOf({ recommended, evaluated });
  const proj = optimizerProjection(allocated);
  const allIds = [...proj.recommended, ...proj.evaluated].map((s) => s.structure_id);
  assert.equal(allIds.length, 44);
  assert.equal(new Set(allIds).size, 44, "no structure may appear in both recommended and evaluated");
  assert.equal(proj.executableTotal, 44);
  const pool = admissibleForMode(allocated, MODE_OPTIMIZER);
  assert.equal(pool.length, 44, "admissibleForMode's own pool (the Full Globe list's source) must equal the same complete total");
});

// 8. Selected identity drives the exact pathway — clicking/selecting a
// specific structure must render THAT structure's own markers/arcs/colour,
// never a different one that merely shares a participant code (the exact
// defect class the marker-click fix in ProjectGlobe.jsx/Workspace.jsx
// closes — this test locks the underlying buildOptimizerPathway/
// optimizerStructureStatus behavior the click handlers both resolve
// through).
test("buildOptimizerPathway: leadingStructureId selects the EXACT structure, and every point/arc in its chain shares its own real recommendation-status colour", () => {
  const best = candidate("best", 500_000, { participants: ["GR", "CA-MB"], primary_jurisdiction: "GR" });
  const otherRecommended = candidate("other-rec", 600_000, { participants: ["IT", "FR"], primary_jurisdiction: "IT" });
  const evalAlt = candidate("eval-1", 900_000, { participants: ["US-GA", "US-NY"], primary_jurisdiction: "US-GA", recommendation_status: "EVALUATED_ALTERNATIVE", is_recommended: false });
  const allocated = allocatedOf({ recommended: [best, otherRecommended], evaluated: [evalAlt] });

  // Selecting the single best/leading recommendation -> every point gold.
  const bestPathway = buildOptimizerPathway(allocated, "best");
  assert.equal(bestPathway.structure.structure_id, "best");
  assert.ok(bestPathway.points.length > 0);
  assert.ok(bestPathway.points.every((p) => p.tier === "gold"), "every point in the BEST recommendation's own chain must be gold");
  assert.ok(bestPathway.arcs.every((a) => a.tier === "gold"));

  // Selecting a DIFFERENT recommended structure -> its own chain, jade
  // throughout (never gold — that is the single best recommendation only —
  // and never silver, which would misrepresent it as an evaluated
  // alternative).
  const otherPathway = buildOptimizerPathway(allocated, "other-rec");
  assert.equal(otherPathway.structure.structure_id, "other-rec", "must resolve the EXACT selected structure, never fall back to a different one");
  assert.ok(otherPathway.points.every((p) => p.tier === "jade"));
  assert.deepEqual(new Set(otherPathway.points.map((p) => p.id)), new Set(["IT", "FR"]), "must render this structure's OWN participants, never a different structure's");

  // Selecting an evaluated alternative -> silver throughout.
  const evalPathway = buildOptimizerPathway(allocated, "eval-1");
  assert.equal(evalPathway.structure.structure_id, "eval-1");
  assert.ok(evalPathway.points.every((p) => p.tier === "silver"));

  // The shared status helper agrees with the pathway's own colouring —
  // marker, route, and (per test 9 below) hover/Inspector can never disagree.
  assert.equal(optimizerStructureStatus(allocated, best), "gold");
  assert.equal(optimizerStructureStatus(allocated, otherRecommended), "jade");
  assert.equal(optimizerStructureStatus(allocated, evalAlt), "silver");
});

// 9. Hover and Inspector use the selected structure — every point's
// attached structureDetail must be the SAME buildCandidateDetail() shape
// (and the SAME real figures) the Inspector opens for that exact structure,
// never a re-derived or partial summary.
test("buildOptimizerPathway: every point's structureDetail is the exact buildCandidateDetail() of the selected structure — hover and Inspector can never disagree", () => {
  const s = candidate("s1", 725_000, {
    participants: ["GR", "CA-MB"], primary_jurisdiction: "GR",
    component_allocations: [
      { jurisdiction_code: "GR", allocated_usd: 400_000, guaranteed_incentive_usd: 120_000, component: "principal" },
      { jurisdiction_code: "CA-MB", allocated_usd: 100_000, guaranteed_incentive_usd: 20_000, component: "vfx" },
    ],
  });
  const allocated = allocatedOf({ recommended: [s] });
  const pathway = buildOptimizerPathway(allocated, "s1");
  const expectedDetail = buildCandidateDetail(s);
  for (const point of pathway.points) {
    assert.deepEqual(point.structureDetail, expectedDetail, "hover's structureDetail must be byte-identical to what the Inspector would show for this same structure");
    assert.equal(point.mode, "optimizer");
    assert.equal(point.optimizerStatus, "gold");
    assert.equal(point.optimizerStatusLabel, OPTIMIZER_SEMANTIC.gold.label);
    assert.equal(point.familyLabel, "Practical Hybrid");
  }
});

// 10. Optimizer's legend vocabulary is genuinely different from Single
// Jurisdiction's, not a relabeled copy — confirms GlobeLegend.jsx actually
// branches (not just that Single Jurisdiction's own labels stay free of
// Optimizer wording, already pinned in single-jurisdiction-globe-wiring-
// closeout.test.mjs).
test("OPTIMIZER_SEMANTIC labels are real and distinct from GLOBE_SEMANTIC's Single Jurisdiction labels, reusing the same four approved hex tokens", () => {
  for (const slot of ["gold", "jade", "silver", "amber"]) {
    assert.equal(OPTIMIZER_SEMANTIC[slot].hex, GLOBE_SEMANTIC[slot].hex, `${slot} must reuse the exact same approved hex, never a new colour`);
    assert.notEqual(OPTIMIZER_SEMANTIC[slot].label, GLOBE_SEMANTIC[slot].label, `${slot}'s Optimizer label must be real, distinct wording from Single Jurisdiction's "${GLOBE_SEMANTIC[slot].label}"`);
  }
  const legendSrc = readSrc("components/GlobeLegend.jsx");
  assert.match(legendSrc, /isOptimizer \? OPTIMIZER_SEMANTIC : GLOBE_SEMANTIC/, "GlobeLegend must actually branch its semantic table on mode, not just its label text");
});

// 11a. Cross-mode leak: switching Single Jurisdiction <-> Optimizer must
// clear the shared, mode-incompatible selection scalars (selectedJurisdiction/
// leadingStructureId/inspector) — source-text pin, since this suite has no
// React state-transition harness (see AppState.jsx's own CODEX_FG-001
// project-boundary reset for the established pattern this mirrors).
test("AppState.jsx's setWorkspaceMode clears selectedJurisdiction/leadingStructureId/inspector on an ACTUAL mode change, never leaking one mode's selection into the other", () => {
  const src = readSrc("state/AppState.jsx");
  const fn = src.match(/const setWorkspaceMode = useCallback\(\(mode\) => \{[\s\S]*?\}, \[projectId, workspaceMode\]\);/);
  assert.ok(fn, "setWorkspaceMode must exist with the expected dependency array");
  assert.match(fn[0], /if \(mode !== workspaceMode\) \{/, "the reset must only fire on an actual mode change, never on every call");
  assert.match(fn[0], /setInspector\(null\)/);
  assert.match(fn[0], /setSelectedJurisdiction\(null\)/);
  assert.match(fn[0], /setLeadingStructureIdRaw\(null\)/);
});

// 11b. Cross-project leak (Optimizer-specific data): a stale leadingStructureId
// from a DIFFERENT project's Optimizer structure must never resolve inside
// this project's pathway — mirrors the same guarantee already proven for
// Single Jurisdiction's best_per_jurisdiction lookups elsewhere; this is the
// Optimizer-pool equivalent, since buildOptimizerPathway resolves against
// THIS allocated's own recommended/evaluated arrays only.
test("buildOptimizerPathway: a leadingStructureId that does not exist in THIS project's Optimizer pool falls back to the top recommendation, never throws or resolves a foreign structure", () => {
  const s = candidate("real-1", 500_000);
  const allocated = allocatedOf({ recommended: [s] });
  const pathway = buildOptimizerPathway(allocated, "structure-from-a-different-project");
  assert.equal(pathway.structure.structure_id, "real-1", "must fall back to this project's own top recommendation, never resolve the foreign id or crash");
});

// Significant defect found and fixed during this pass's own live Phase 9
// verification (see this file's header comment for the full root-cause
// narrative): Globe3D.jsx's marker click/hover handlers must read through
// liveRef at call time, never the raw onPointClick/onPointHover props
// directly, because the hit-target factory that wires them up lives inside
// a mount-only effect and would otherwise run the FIRST render's stale
// selectJurisdiction/globeMode closure forever, for the life of the mounted
// component — invisible in a single-mode session, but silently wrong on
// EVERY marker click after any mode switch within the same page load.
test("Globe3D.jsx's hit-target click/hover listeners read onPointClick/onPointHover through liveRef, never the closed-over prop directly", () => {
  const src = readSrc("components/Globe3D.jsx");
  const liveRefDecl = src.match(/const liveRef = useRef\(\{[^}]*\}\);/);
  assert.ok(liveRefDecl, "liveRef must exist");
  assert.match(liveRefDecl[0], /onPointClick: null/, "liveRef must carry onPointClick");
  assert.match(liveRefDecl[0], /onPointHover: null/, "liveRef must carry onPointHover");
  // A dedicated effect keeps liveRef current on every render (unlike the
  // mount-only graph-setup effect below it).
  assert.match(src, /useEffect\(\(\) => \{\s*\n\s*liveRef\.current\.onPointClick = onPointClick;\s*\n\s*liveRef\.current\.onPointHover = onPointHover;\s*\n\s*\}, \[onPointClick, onPointHover\]\);/);
  // The hit-target factory itself must call through liveRef, never the
  // closed-over props — this factory is defined inside the mount-only
  // (`}, []`) effect, so a direct reference would be permanently stale.
  const factory = src.match(/\.htmlElement\(\(d\) => \{[\s\S]*?return el;\s*\n\s*\}\);/);
  assert.ok(factory, "the hit-target factory must exist");
  assert.match(factory[0], /liveRef\.current\.onPointClick\?\.\(d\)/);
  assert.match(factory[0], /liveRef\.current\.onPointHover\?\.\(d, el\.getBoundingClientRect\(\)\)/);
  assert.match(factory[0], /liveRef\.current\.onPointHover\?\.\(null\)/);
  assert.doesNotMatch(factory[0], /(?<!liveRef\.current\.)onPointClick\(d\)/, "must never call the raw prop directly inside the mount-only factory");
  assert.doesNotMatch(factory[0], /(?<!liveRef\.current\.)onPointHover\(/, "must never call the raw prop directly inside the mount-only factory");
});
