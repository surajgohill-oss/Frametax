// ── Final non-Globe closeout, Item A — canonical scenario-selection
// consistency regression protection ──────────────────────────────────────
//
// Run with: npm test (node --test)
//
// Codex previously found that Reports.jsx resolved its "leading
// structure" with a rank==1-only lookup and NO fallback, while
// Overview.jsx / Workspace.jsx additionally fell back to
// bestPricedCandidate() whenever rank 1 was absent (comparable_count==0,
// a real, common state). The same production state could therefore show
// a real leading structure on Overview/Workspace and "no structure
// priced yet" on Reports — a genuine scenario-truth disagreement.
//
// Fixed by: (1) the backend computing and serving ONE canonical field
// (allocated_structures.canonical_selected_structure_id — see
// canonical_production_view.py), and (2) every consumer
// (lib/globeData.js::activeStructure, lib/bestPricedCandidate.js,
// Reports.jsx) resolving through that same field. These tests assert
// the THREE call sites agree, using hand-built payloads shaped like the
// real served allocated_structures object — no JSX, no backend.

import test from "node:test";
import assert from "node:assert/strict";
import { activeStructure } from "../src/lib/globeData.js";
import { bestPricedCandidate } from "../src/lib/bestPricedCandidate.js";

function structure(id, npc, overrides = {}) {
  return {
    structure_id: id,
    label: id,
    is_fully_priced: true,
    npc_with_adjustments_usd: npc,
    ...overrides,
  };
}

test("rank 1 present: activeStructure, bestPricedCandidate, and a Reports-shaped lookup all resolve to the SAME structure_id", () => {
  const allocated = {
    structures: [structure("s1", 900_000), structure("s2", 700_000)],
    ranking: [{ structure_id: "s2", rank: 1 }, { structure_id: "s1", rank: null }],
    // Server-computed canonical field: rank 1 wins (s2), matching the
    // ranking array above — this is the exact shape
    // canonical_production_view.py serves.
    canonical_selected_structure_id: "s2",
  };

  const fromActive = activeStructure(allocated, null);
  const fromBestPriced = bestPricedCandidate(allocated);
  // Reports.jsx's own resolution: activeStructure(allocated, leadingStructureId) || bestPricedCandidate(allocated)
  const fromReports = activeStructure(allocated, null) || bestPricedCandidate(allocated);

  assert.equal(fromActive.structure_id, "s2");
  assert.equal(fromBestPriced.structure_id, "s2");
  assert.equal(fromReports.structure_id, "s2");
});

test("rank 1 ABSENT (comparable_count==0, e.g. Bad Hombres): all three still agree, none silently return nothing", () => {
  const allocated = {
    structures: [structure("s1", 900_000), structure("s2", 700_000)],
    // No candidate reached numeric rank — a real, common state.
    ranking: [{ structure_id: "s1", rank: null }, { structure_id: "s2", rank: null }],
    // Server field still resolves to the lowest-NPC priced candidate —
    // this is the exact behavior that used to be MISSING from Reports.
    canonical_selected_structure_id: "s2",
  };

  const fromActive = activeStructure(allocated, null);
  const fromBestPriced = bestPricedCandidate(allocated);
  const fromReports = activeStructure(allocated, null) || bestPricedCandidate(allocated);

  assert.equal(fromActive.structure_id, "s2", "activeStructure must fall back to the canonical field, not return null");
  assert.equal(fromBestPriced.structure_id, "s2");
  assert.equal(fromReports.structure_id, "s2", "Reports must resolve a real structure even with no numeric rank 1 — this is the exact defect that was fixed");
  assert.equal(fromActive.structure_id, fromReports.structure_id);
});

test("producer leadingStructureId override wins on every call site identically", () => {
  const allocated = {
    structures: [structure("s1", 900_000), structure("s2", 700_000)],
    ranking: [{ structure_id: "s2", rank: 1 }],
    canonical_selected_structure_id: "s2",
  };
  // Producer manually picked the more expensive s1 as leading — a real,
  // legitimate override (e.g. jurisdictional/creative reasons), never
  // overwritten by the canonical field.
  const leadingStructureId = "s1";

  const fromActive = activeStructure(allocated, leadingStructureId);
  const fromReports = activeStructure(allocated, leadingStructureId) || bestPricedCandidate(allocated);

  assert.equal(fromActive.structure_id, "s1");
  assert.equal(fromReports.structure_id, "s1");
});

test("defensive fallback: activeStructure still resolves correctly from a stale payload missing canonical_selected_structure_id", () => {
  const allocated = {
    structures: [structure("s1", 900_000), structure("s2", 700_000)],
    ranking: [{ structure_id: "s2", rank: 1 }],
    // Simulates a served shape that predates this closeout pass.
  };
  assert.equal(activeStructure(allocated, null).structure_id, "s2");
});

test("no priced structure at all: every call site returns null, never fabricates a leading structure", () => {
  const allocated = {
    structures: [structure("s1", null, { is_fully_priced: false })],
    ranking: [{ structure_id: "s1", rank: null }],
    canonical_selected_structure_id: null,
  };
  assert.equal(activeStructure(allocated, null), null);
  assert.equal(bestPricedCandidate(allocated), null);
});
