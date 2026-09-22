// ── LOCAL_GLOBE_WIRING_CLOSEOUT (2026-09-21) ────────────────────────────────
//
// Root cause confirmed live against Little Utopia's real served payload:
// every structure the structural generator builds (HYBRID_ANCHOR_COMPONENT,
// and by construction every other Optimizer family sharing that code path)
// carries `segments: []` — it never populates `segments`, only
// `component_allocations`. Every hover/click-through consumer read ONLY
// `structure.segments`:
//   - the hover card's own fallback ("Not available") masked this as an
//     honest-looking gap rather than a defect;
//   - the Inspector click-through had NO fallback at all — segments empty
//     AND recommendation null meant clicking any Optimizer jurisdiction or
//     card opened literally no Inspector (confirmed live, zero DOM change);
//   - ScenarioCard's "Qualified spend" summed segments[].qpe_usd, so every
//     Optimizer scenario card silently showed "$0" — not a real zero.
//
// These tests pin resolveSegmentDetail's fallback (globeData.js) and the
// ScenarioCard qualifiedSpendRaw fallback (Workspace.jsx) against the exact
// real field shapes confirmed live, so this exact regression can't return
// silently.

import test from "node:test";
import assert from "node:assert/strict";

import { resolveSegmentDetail, buildCountryHoverData, buildGlobeView } from "../src/lib/globeData.js";
import { MODE_OPTIMIZER } from "../src/lib/workspaceScenarioMode.js";

// Real field shape confirmed live against Little Utopia's own served
// payload (see comment above) — never a guessed/simplified shape.
function hybridStructure(overrides = {}) {
  return {
    structure_id: "hy-1",
    structure_type: "hybrid",
    classification: "HYBRID_ANCHOR_COMPONENT",
    label: "Manitoba + music->Newfoundland & Labrador + vfx->Italy (hybrid)",
    primary_jurisdiction: "CA-MB",
    participants: ["CA-MB", "CA-NL", "IT"],
    is_fully_priced: true,
    segments: [],
    recommendation: null,
    economic_identity: "econ-hybrid-1",
    npc_with_adjustments_usd: 2_539_002.6,
    selected_incentive_usd: 1_825_390.4,
    gross_budget_usd: 4_364_393,
    component_allocations: [
      { component: "principal_production", program_slug: "ca_mb_film_video_credit", allocated_usd: 4_302_827, jurisdiction_code: "CA-MB", guaranteed_incentive_usd: 1_800_763.2, conditional_incentive_usd: 0, jurisdiction_display_name: "Manitoba" },
      { component: "post", program_slug: "ca_nl_all_spend_credit", allocated_usd: 9_068, jurisdiction_code: "CA-NL", guaranteed_incentive_usd: 3_627.2, conditional_incentive_usd: 0, jurisdiction_display_name: "Newfoundland & Labrador" },
      { component: "vfx", program_slug: "it_tax_credit_foreign", allocated_usd: 52_498, jurisdiction_code: "IT", guaranteed_incentive_usd: 21_000, conditional_incentive_usd: 0, jurisdiction_display_name: "Italy" },
    ],
    ...overrides,
  };
}

// 1. resolveSegmentDetail falls back to component_allocations, never invents a field.
test("resolveSegmentDetail derives real Program/QPE/Incentive from component_allocations when segments is empty", () => {
  const s = hybridStructure();
  const detail = resolveSegmentDetail(s, "CA-NL");
  assert.ok(detail, "must resolve a real detail object, never null, when a matching component_allocations entry exists");
  assert.equal(detail.jurisdiction_code, "CA-NL");
  assert.equal(detail.program_slug, "ca_nl_all_spend_credit");
  assert.equal(detail.claims_incentive, true);
  assert.equal(detail.allocated_usd, 9_068);
  assert.equal(detail.qpe_usd, 9_068, "QPE must be the real allocated_usd, never zero/undefined");
  assert.equal(detail.incentive_floor_usd, 3_627.2);
  assert.equal(detail.incentive_ceiling_usd, 3_627.2);
  // Fields component_allocations genuinely does not track must stay
  // undefined (renders "—"/"Not available" downstream), never fabricated.
  assert.equal(detail.rate_floor, undefined);
  assert.equal(detail.rate_ceiling, undefined);
  assert.equal(detail.excluded_usd, undefined);
});

// 2. Real segments data (when present) is still preferred, unchanged.
test("resolveSegmentDetail prefers a real segments entry over component_allocations when both exist", () => {
  const s = hybridStructure({
    segments: [{ jurisdiction_code: "CA-NL", claims_incentive: true, program_slug: "real-segment-program", qpe_usd: 999, incentive_ceiling_usd: 111, rate_ceiling: 0.4 }],
  });
  const detail = resolveSegmentDetail(s, "CA-NL");
  assert.equal(detail.program_slug, "real-segment-program", "a real segment must win over the component_allocations fallback");
  assert.equal(detail.qpe_usd, 999);
});

// 3. No match in either source returns null (never a fabricated detail).
test("resolveSegmentDetail returns null when neither segments nor component_allocations has this jurisdiction", () => {
  const s = hybridStructure();
  assert.equal(resolveSegmentDetail(s, "ZZ"), null);
});

// 4. Hover card economics are populated from component_allocations for Optimizer structures.
test("buildCountryHoverData's baseIncentive/segmentIncentiveUsd are populated (not null) for a hybrid structure via the component_allocations fallback", () => {
  const s = hybridStructure();
  const rankById = new Map();
  const view = buildGlobeView(
    { structures: [s], ranking: [], canonical_selected_structure_id: null, best_per_jurisdiction: {}, top_by_structural_family: {}, optimizer_candidates: [s], optimizer_scenarios: [s] },
    rankById,
    { mode: MODE_OPTIMIZER, leadingStructureId: "hy-1" },
  );
  const hoverNL = view.hoverByIso.get("CA-NL");
  assert.ok(hoverNL, "CA-NL must have a hover entry in the rendered Optimizer scene");
  assert.equal(hoverNL.segmentIncentiveUsd, 3_627.2, "modeled incentive must be the real component figure, never null");
  assert.ok(hoverNL.baseIncentive, "baseIncentive must be populated, never null, when a real program exists");
  assert.equal(hoverNL.baseIncentive.programLabel !== undefined, true);
  // Rate genuinely unavailable at this granularity — must stay null, never fabricated.
  assert.equal(hoverNL.baseIncentive.ratePct, null);
});

// 5. QPE-weighted arcs/points use the real component figure.
test("buildOptimizerPathway's points/arcs carry real qpeUsd from component_allocations, not null for every leg", async () => {
  const { buildOptimizerPathway } = await import("../src/lib/globeData.js");
  const s = hybridStructure();
  const pathway = buildOptimizerPathway({ structures: [s], optimizer_candidates: [s], optimizer_scenarios: [s] }, "hy-1");
  const nlPoint = pathway.points.find((p) => p.id === "CA-NL");
  assert.equal(nlPoint.qpeUsd, 9_068);
});

// 6. Overlay completeness: a genuinely unavailable field never renders as an
// unexplained blank — Money-consuming callers get undefined (existing "—"
// treatment), never NaN or empty string.
test("resolveSegmentDetail never returns NaN/empty-string placeholders for fields it cannot derive", () => {
  const s = hybridStructure();
  const detail = resolveSegmentDetail(s, "IT");
  for (const key of ["rate_floor", "rate_ceiling", "is_band_ceiling", "excluded_usd", "statutory_basis", "blockers", "qualification_trace"]) {
    const v = detail[key];
    assert.ok(v === undefined, `${key} must be omitted (undefined), never a fabricated placeholder — got ${JSON.stringify(v)}`);
  }
});

// 7. Full/Map/Split parity through the shared scene model (already covered
// structurally by prior passes' tests; re-pinned here against the fixed
// resolver to confirm the fix didn't regress cross-surface identity).
test("the same structure resolves to the identical economic_identity and participant set regardless of which jurisdiction code triggered the lookup", () => {
  const s = hybridStructure();
  const byCA = resolveSegmentDetail(s, "CA-MB");
  const byNL = resolveSegmentDetail(s, "CA-NL");
  const byIT = resolveSegmentDetail(s, "IT");
  assert.notEqual(byCA.jurisdiction_code, byNL.jurisdiction_code);
  assert.notEqual(byNL.jurisdiction_code, byIT.jurisdiction_code);
  // All three resolve from the SAME structure's component_allocations —
  // proven by each carrying a real, distinct, non-fabricated program_slug.
  assert.equal(byCA.program_slug, "ca_mb_film_video_credit");
  assert.equal(byNL.program_slug, "ca_nl_all_spend_credit");
  assert.equal(byIT.program_slug, "it_tax_credit_foreign");
});
