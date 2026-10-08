// Direct Company Globe entry (2026-10-08): with an EMPTY client leading-selection store the scene must still resolve every
// active project from the single aggregate payload, and the side list and the Globe must share one rows array.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { buildCompanyScene } from "../src/lib/companyScene.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const comp = (component, jurisdiction_code) => ({ component, jurisdiction_code, allocated_usd: 1000 });
const payload = [
  { project_id: "bh", title: "Bad Hombres", lifecycle: "EVALUATION", baseline_jurisdiction: "US-NM", home_code: "US-NM", leading: { structure: { classification: "SINGLE_JURISDICTION", participants: ["US-NM"], primary_jurisdiction: "US-NM", component_allocations: [] } } },
  { project_id: "fvd", title: "FVD", lifecycle: "EVALUATION", baseline_jurisdiction: "GR", home_code: "GR", leading: { structure: { classification: "HYBRID_ANCHOR_COMPONENT", participants: ["GR", "RO"], primary_jurisdiction: "GR", component_allocations: [comp("principal_production", "GR"), comp("post_vfx_package", "RO")] } } },
  { project_id: "lls", title: "LLS", lifecycle: "EVALUATION", baseline_jurisdiction: "US-CA", home_code: "US-CA", leading: { structure: { classification: "SINGLE_JURISDICTION", participants: ["US-CA"], primary_jurisdiction: "US-CA", component_allocations: [] } } },
  { project_id: "lu", title: "LU", lifecycle: "EVALUATION", baseline_jurisdiction: "MU", home_code: "MU", leading: { structure: { classification: "HYBRID_ANCHOR_COMPONENT", participants: ["MU", "ZA"], primary_jurisdiction: "MU", component_allocations: [comp("principal_production", "MU"), comp("post_vfx_package", "ZA")] } } },
];

// Same row shape CompanyGlobe.withLeading produces when the store has no entry (a fresh tab).
const rowsFromPayload = (projects) => projects.map((row) => ({
  project: { id: row.project_id, title: row.title, lifecycle: row.lifecycle },
  homeCode: row.home_code, structure: row.leading?.structure ?? null,
  principal: row.leading?.structure?.primary_jurisdiction ?? row.baseline_jurisdiction,
}));

test("empty client store: every active project still renders from the aggregate payload alone", () => {
  // buildCompanyScene takes only the resolved rows: it cannot read (or depend on) the session leading-selection store.
  assert.doesNotMatch(readFileSync(join(SRC, "lib/companyScene.js"), "utf8"), /leadingSelection/);
  const rows = rowsFromPayload(payload);
  const scene = buildCompanyScene(rows, () => "#4a7bd0");
  assert.equal(rows.length, 4);
  assert.deepEqual([...new Set(scene.points.map((p) => p.projectId))].sort(), ["bh", "fvd", "lls", "lu"]);
  for (const k of ["US-NM", "US-CA", "GR", "RO", "MU", "ZA"]) assert.ok(scene.polygonColors.has(k), `${k} territory painted`);
  assert.equal(scene.arcs.length, 2, "one hybrid route each for FVD and LU; single-jurisdiction projects have no route");
  assert.deepEqual(scene.routeLabels.map((l) => l.text), ["POST/VFX", "POST/VFX"]);
  assert.ok(scene.points.every((p) => p.iso), "markers carry the canonical key so polygon hover resolves");
});

test("side list and Globe consume the same rows array and the screen never reads per-project state", () => {
  const src = readFileSync(join(SRC, "screens/company/CompanyGlobe.jsx"), "utf8");
  assert.match(src, /buildCompanyScene\(rows,/);
  assert.equal((src.match(/rows\.map\(/g) || []).length, 1, "the list maps rows; the scene is built from the same rows");
  assert.match(src, /autoHeight/, "the canvas fills its panel so route labels project against the rendered size");
  assert.doesNotMatch(src, /getProjectState|useCineGlobe|Promise\.all/);
});

test("a project with no evaluated structure falls back to its baseline territory only", () => {
  const rows = rowsFromPayload([{ project_id: "x", title: "X", lifecycle: "EVALUATION", baseline_jurisdiction: "GR", home_code: "GR", leading: { structure: null } }]);
  const scene = buildCompanyScene(rows, () => "#4a7bd0");
  assert.deepEqual(scene.points.map((p) => p.code), ["GR"]);
  assert.deepEqual(scene.arcs, []);
});
