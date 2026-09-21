// ── CODEX_FG-002 (2026-09-21) ───────────────────────────────────────────────
//
// Focused tests for buildCandidateDetail(), the one canonical structure-level
// adapter introduced this task so every "select a whole card/structure" entry
// point (ProjectGlobe.selectStructure, Workspace.handleSelectStructure) opens
// the SAME complete structure identity instead of an arbitrarily-chosen
// non-primary participant's segment. See globeData.js's own header comment
// above buildCandidateDetail for the full root-cause narrative (confirmed
// live: an Alabama-primary Optimizer candidate previously opened Manitoba's
// segment Inspector because the prior code inferred identity from
// `participants.find(c => c !== primary)`).
//
// Pins two behaviors specifically:
//   1. Same-jurisdiction program stacks (e.g. Ontario OFTTC + OCASE) must
//      NOT be deduped down to one row — every real segment/component row
//      survives, even when several share a jurisdiction_code.
//   2. Never fabricate a field the source lacks (segments vs
//      component_allocations fallback) — missing values stay null/undefined,
//      never silently substituted from another row.

import test from "node:test";
import assert from "node:assert/strict";

import { buildCandidateDetail } from "../src/lib/globeData.js";

test("buildCandidateDetail preserves every same-jurisdiction segment (no dedup by code)", () => {
  const structure = {
    structure_id: "s-ontario-stack",
    economic_identity: "abc123",
    structure_type: "combined",
    classification: "STACKED_PROGRAMS",
    label: "Ontario OFTTC + OCASE",
    primary_jurisdiction: "CA-ON",
    participants: ["CA-ON"],
    program_slugs: ["on_ofttc", "on_ocase"],
    is_fully_priced: true,
    candidate_status: "PRICED",
    selected_incentive_usd: 5238336.62,
    npc_with_adjustments_usd: 6745317.38,
    blockers: [],
    warnings: [],
    segments: [
      { jurisdiction_code: "CA-ON", program_slug: "on_ofttc", qpe_usd: 9883654, incentive_ceiling_usd: 3459278.9, claims_incentive: true },
      { jurisdiction_code: "CA-ON", program_slug: "on_ocase", qpe_usd: 9883654, incentive_ceiling_usd: 1779057.72, claims_incentive: true },
    ],
    component_allocations: [],
  };

  const detail = buildCandidateDetail(structure);

  assert.equal(detail.components.length, 2, "both CA-ON rows must survive — dedup-by-code would collapse this to 1");
  assert.deepEqual(detail.components.map((c) => c.program_slug), ["on_ofttc", "on_ocase"]);
  // totalQpe sums each row's own qpe_usd — never divides or dedups the shared budget base.
  assert.equal(detail.qpe_usd, 9883654 + 9883654);
  assert.equal(detail.incentive_usd, 5238336.62);
  assert.equal(detail.npc_usd, 6745317.38);
});

test("buildCandidateDetail falls back to component_allocations only when segments is empty, without fabricating segment-only fields", () => {
  const structure = {
    structure_id: "s-optimizer-hybrid",
    economic_identity: "def456",
    structure_type: "hybrid",
    classification: "HYBRID_ANCHOR_COMPONENT",
    label: "Manitoba + Italy (hybrid)",
    primary_jurisdiction: "CA-MB",
    participants: ["CA-MB", "IT"],
    program_slugs: [],
    is_fully_priced: true,
    candidate_status: "PRICED",
    selected_incentive_usd: 4435305.6,
    npc_with_adjustments_usd: 7548348.4,
    blockers: [],
    warnings: [],
    segments: [],
    component_allocations: [
      { jurisdiction_code: "CA-MB", program_slug: "ca_mb_film_video_credit", component: "principal_production", allocated_usd: 11736880, guaranteed_incentive_usd: 4336596 },
      { jurisdiction_code: "IT", program_slug: "it_tax_credit_foreign", component: "vfx", allocated_usd: 40000, guaranteed_incentive_usd: 16000 },
    ],
  };

  const detail = buildCandidateDetail(structure);

  assert.equal(detail.components.length, 2);
  // component_allocations rows have no real rate_floor/rate_ceiling — must stay null, never invented.
  assert.equal(detail.components[0].rate_floor, null);
  assert.equal(detail.components[0].rate_ceiling, null);
  assert.equal(detail.components[0].component, "principal_production");
  assert.equal(detail.qpe_usd, 11736880 + 40000);
});

test("buildCandidateDetail returns null for a null structure, never throws", () => {
  assert.equal(buildCandidateDetail(null), null);
  assert.equal(buildCandidateDetail(undefined), null);
});

test("buildCandidateDetail never invents participants/blockers/warnings the structure doesn't serve", () => {
  const structure = {
    structure_id: "s-minimal",
    economic_identity: "ghi789",
    primary_jurisdiction: "GR",
    segments: [],
    component_allocations: [],
  };
  const detail = buildCandidateDetail(structure);
  assert.deepEqual(detail.participants, []);
  assert.deepEqual(detail.blockers, []);
  assert.deepEqual(detail.warnings, []);
  assert.deepEqual(detail.components, []);
  assert.equal(detail.qpe_usd, 0);
});
