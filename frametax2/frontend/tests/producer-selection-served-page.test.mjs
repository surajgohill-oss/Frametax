// NA25_SELECTION_AND_ALLOCATION_INTEGRITY_REPAIR -- consumer side of the pinned producer selection.
// The backend now serves the producer's selected structure on the first candidate page (canonical_production_view._pinned);
// these controls assert the Overview / Workspace / Reports resolver chain returns exactly that structure, claims "user"
// only for a structure that is actually served, and never presents a substitute as the producer's selection.
import test from "node:test";
import assert from "node:assert/strict";
import { activeStructure } from "../src/lib/globeData.js";
import { resolveLeadingStructure } from "../src/lib/leadingResolve.js";

const structure = (id, npc, extra = {}) => ({ structure_id: id, label: id, is_fully_priced: true, npc_with_adjustments_usd: npc, ...extra });

// Served shape: baseline + canonical leader + the producer's pick pinned ahead of rank order (a pick whose rank is beyond page one).
const served = () => ({
  structures: [structure("baseline", 900_000, { is_baseline: true }), structure("pick", 880_000), structure("s2", 700_000)],
  ranking: [{ structure_id: "s2", rank: 1 }, { structure_id: "baseline", rank: null }, { structure_id: "pick", rank: null }],
  canonical_selected_structure_id: "s2",
});

test("a served producer pick is the structure Overview, Workspace and Reports resolve, claimed as the user's choice", () => {
  const allocated = served();
  assert.equal(activeStructure(allocated, "pick").structure_id, "pick");
  const resolved = resolveLeadingStructure(allocated, "pick");
  assert.equal(resolved.structure.structure_id, "pick");
  assert.equal(resolved.source, "user");
});

test("a pick that is not served is never presented as the producer's selection (no substitute is labelled 'user')", () => {
  const allocated = served();
  const resolved = resolveLeadingStructure(allocated, "not-served");
  assert.equal(resolved.source, "baseline");
  assert.equal(resolved.structure, null);
});
