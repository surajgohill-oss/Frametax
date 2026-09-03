// ── F#K Valentine's Day economic/semantic regression fix (2026-09-03) —
// focused regression protection for invariants A-H ─────────────────────
//
// Run with: npm test (node --test)
//
// Pure logic tests — no JSX, no backend, no live economics. Every input
// is a hand-built structure shaped like the real canonical_evaluation.py
// served payload. This file protects the specific defects traced and
// fixed for F#K Valentine's Day (project 6c6f1c13-2d49-4bbc-bafb-
// 2a12efa93112): Saudi Arabia's discretionary/preapproval risk not
// surfacing (item 3) and Manitoba's fabricated $16.1M program-cap sum
// (item 4b). Generic across any jurisdiction — no test here asserts on
// "Saudi" or "Manitoba" by name in the source code, only on behavior.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { hasAdministrativeAllocationRisk } from "../src/lib/allocationRisk.js";
import { selectMaxPotentialCard } from "../src/lib/productionOptions.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

function structure(overrides) {
  return {
    structure_id: "s1",
    structure_type: "full_relocation",
    label: "Base",
    primary_jurisdiction: "US",
    participants: ["US"],
    is_fully_priced: true,
    is_baseline: false,
    treaty_slug: null,
    gross_budget_usd: 1_000_000,
    selected_incentive_usd: 300_000,
    npc_with_adjustments_usd: 700_000,
    conditional_programs: [],
    segments: [],
    warnings: [],
    ...overrides,
  };
}

function allocated(structures, ranking) {
  return {
    structures,
    ranking: ranking || structures.map((s, i) => ({ structure_id: s.structure_id, rank: i + 1, is_fully_priced: s.is_fully_priced })),
  };
}

// ── Invariant F: a conditional/discretionary/preapproval-gated structure
// must never be indistinguishable from an unconditional deterministic
// winner (item 3 — Saudi Arabia's real defect). ──────────────────────────
test("hasAdministrativeAllocationRisk: true for a structure carrying the backend's real disclosure prefix", () => {
  const gated = structure({
    warnings: [
      "Administrative/allocation risk (not an economic block -- the figures below are this program's real deterministic formula, priced normally): the award authority has discretion over whether and/or how much to award; a preapproval/certification step (e.g. an allocation letter) is required before this incentive is confirmed.",
    ],
  });
  assert.equal(hasAdministrativeAllocationRisk(gated), true);
});

test("hasAdministrativeAllocationRisk: false for a structure with no warnings, or warnings that are real but unrelated", () => {
  assert.equal(hasAdministrativeAllocationRisk(structure({ warnings: [] })), false);
  assert.equal(hasAdministrativeAllocationRisk(structure({ warnings: undefined })), false);
  assert.equal(
    hasAdministrativeAllocationRisk(structure({ warnings: ["Travel/FX/local-cost (MFNI) normalization ARE applied."] })),
    false,
    "an unrelated real disclosure must never be mistaken for allocation risk"
  );
});

test("hasAdministrativeAllocationRisk: generic — detects the risk regardless of which jurisdiction/program carries it, never string-matches a country name", () => {
  const anyCountryGated = structure({
    primary_jurisdiction: "ZZ", // deliberately not a real code — proves detection is prefix-only
    warnings: ["Administrative/allocation risk (not an economic block -- ...): allocation is competitive/capacity-limited."],
  });
  assert.equal(hasAdministrativeAllocationRisk(anyCountryGated), true);
});

// ── Invariant D: a program-level cap/ceiling must never be presented as
// this project's calculated incentive (item 4b — Manitoba's real
// defect: 6 unrelated funds' own per-project caps summed to $16.1M for a
// $4.5M-budget production). ──────────────────────────────────────────────
test("selectMaxPotentialCard: never exposes a summed program-cap dollar figure as this project's potential", () => {
  const withFunds = structure({
    structure_id: "opportunity",
    conditional_programs: [
      { program_name: "Regional Fund", documented_cap_usd: 8_000_000 },
      { program_name: "National Fund", documented_cap_usd: 8_100_000 },
    ],
  });
  const result = selectMaxPotentialCard(allocated([withFunds, structure({ structure_id: "plain" })]), new Set());
  assert.equal(result.potentialUsd, null, "a program's own cap-sum must never be shown as this project's dollar potential");
  // The real, truthful facts (fund count / names) are still surfaced —
  // disclosure without fabrication.
  assert.equal(result.fundCount, 2);
  assert.deepEqual(result.fundNames, ["Regional Fund", "National Fund"]);
});

test("selectMaxPotentialCard: a disclosed cap total can economically exceed the production's own gross budget without ever being displayed as achievable incentive", () => {
  // Exactly the shape of the real Manitoba defect: gross_budget_usd here
  // (1,000,000) is far smaller than the summed documented_cap_usd
  // (16,100,000) — proving the selection signal and the DISPLAY value
  // are correctly decoupled.
  const withFunds = structure({
    structure_id: "opportunity",
    gross_budget_usd: 1_000_000,
    conditional_programs: [
      { program_name: "Fund A", documented_cap_usd: 6_000_000 },
      { program_name: "Fund B", documented_cap_usd: 5_100_000 },
      { program_name: "Fund C", documented_cap_usd: 5_000_000 },
    ],
  });
  const result = selectMaxPotentialCard(allocated([withFunds]), new Set());
  assert.equal(result.structure.structure_id, "opportunity", "the cap-sum ranking signal still selects the strongest disclosed opportunity");
  assert.equal(result.potentialUsd, null, "regardless of how large the disclosed cap sum is, it is never rendered as a dollar figure");
});

// ── IncentiveIntelligence.jsx and Workspace.jsx must both consume the
// SAME generic detector — never a second, independently-maintained
// Saudi-specific (or any-jurisdiction-specific) check. ───────────────────
test("IncentiveIntelligence.jsx and Workspace.jsx both read hasAdministrativeAllocationRisk from the shared lib, never a hardcoded jurisdiction check", () => {
  const iiSrc = read("components/IncentiveIntelligence.jsx");
  const wsSrc = read("screens/production/Workspace.jsx");
  assert.match(iiSrc, /hasAdministrativeAllocationRisk/);
  assert.match(wsSrc, /hasAdministrativeAllocationRisk/);
  for (const src of [iiSrc, wsSrc]) {
    assert.ok(!/["']SA["']|Saudi/i.test(src), "must never hardcode Saudi-specific UI behavior");
  }
});

// ── ProductionHero.jsx (the Hero's "Top Priced Candidate" / most
// visible unconditional-winner surface) must also read the same
// generic detector. ───────────────────────────────────────────────────
test("ProductionHero.jsx surfaces the same generic allocation-risk detector on its headline candidate, never hardcoded per-jurisdiction", () => {
  const src = read("components/ProductionHero.jsx");
  assert.match(src, /hasAdministrativeAllocationRisk/);
  assert.ok(!/["']SA["']|Saudi/i.test(src), "must never hardcode Saudi-specific UI behavior");
});
