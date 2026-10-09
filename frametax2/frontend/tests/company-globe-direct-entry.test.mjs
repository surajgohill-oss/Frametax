// Direct Company Globe entry (2026-10-08): with an EMPTY client leading-selection store the scene must still resolve every
// active project from the single aggregate payload, and the side list and the Globe must share one rows array.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { buildCompanyScene, buildPortfolioMiniOverlay } from "../src/lib/companyScene.js";
import { portfolioRows, resolvePortfolioRow } from "../src/lib/portfolioRows.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const comp = (component, jurisdiction_code) => ({ component, jurisdiction_code, allocated_usd: 1000 });
const payload = [
  { project_id: "bh", title: "Bad Hombres", lifecycle: "EVALUATION", baseline_jurisdiction: "US-NM", home_code: "US-NM", leading: { structure: { classification: "SINGLE_JURISDICTION", participants: ["US-NM"], primary_jurisdiction: "US-NM", component_allocations: [] } } },
  { project_id: "fvd", title: "FVD", lifecycle: "EVALUATION", baseline_jurisdiction: "GR", home_code: "GR", leading: { structure: { classification: "HYBRID_ANCHOR_COMPONENT", participants: ["GR", "RO"], primary_jurisdiction: "GR", component_allocations: [comp("principal_production", "GR"), comp("post_vfx_package", "RO")] } } },
  { project_id: "lls", title: "LLS", lifecycle: "EVALUATION", baseline_jurisdiction: "US-CA", home_code: "US-CA", leading: { structure: { classification: "SINGLE_JURISDICTION", participants: ["US-CA"], primary_jurisdiction: "US-CA", component_allocations: [] } } },
  { project_id: "lu", title: "LU", lifecycle: "EVALUATION", baseline_jurisdiction: "MU", home_code: "MU", leading: { structure: { classification: "HYBRID_ANCHOR_COMPONENT", participants: ["MU", "ZA"], primary_jurisdiction: "MU", component_allocations: [comp("principal_production", "MU"), comp("post_vfx_package", "ZA")] } } },
];

const rowsFromPayload = (projects, sel = () => null) => portfolioRows({ projects }, sel);

test("empty client store: every active project still renders from the aggregate payload alone", () => {
  // buildCompanyScene takes only the resolved rows: it cannot read (or depend on) the session leading-selection store.
  assert.doesNotMatch(readFileSync(join(SRC, "lib/companyScene.js"), "utf8"), /leadingSelection/);
  const rows = rowsFromPayload(payload);
  const scene = buildCompanyScene(rows);
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
  assert.match(src, /portfolioRows\(portfolio/, "rows come from the shared resolver");
  assert.equal((src.match(/rows\.map\(/g) || []).length, 1, "the list maps rows; the scene is built from the same rows");
  assert.match(src, /autoHeight/, "the canvas fills its panel so route labels project against the rendered size");
  assert.doesNotMatch(src, /getProjectState|useCineGlobe|Promise\.all/);
});

test("a project with no evaluated structure falls back to its baseline territory only", () => {
  const rows = rowsFromPayload([{ project_id: "x", title: "X", lifecycle: "EVALUATION", baseline_jurisdiction: "GR", home_code: "GR", leading: { structure: null } }]);
  const scene = buildCompanyScene(rows);
  assert.deepEqual(scene.points.map((p) => p.code), ["GR"]);
  assert.deepEqual(scene.arcs, []);
});

// The stage lookup CompanyGlobe injects (PROJECT_STATUSES tier -> stage token); every active project is in Evaluation today.
const STAGE = { evaluation: { key: "evaluation", label: "Evaluation", hex: "#6FA0D6" }, production: { key: "production", label: "Production", hex: "#E8C273" } };
const stageOf = (p) => STAGE[(p.lifecycle || "EVALUATION").toLowerCase()] || STAGE.evaluation;

test("colour is the production STAGE: all-Evaluation projects share the Evaluation blue on every scene element, truthfully", () => {
  const scene = buildCompanyScene(rowsFromPayload(payload), { stageOf });
  assert.deepEqual([...scene.stageCounts], [["evaluation", 4]]);
  assert.ok(scene.points.every((p) => p.color === "#6FA0D6"), "markers");
  assert.ok(scene.arcs.every((a) => a.color[0] === "#6FA0D6"), "routes");
  assert.ok(scene.routeLabels.every((l) => l.color === "#6FA0D6"), "route labels");
  assert.equal(scene.polygonColors.get("US-NM"), "#6FA0D6", "principal territory fill");
  assert.notEqual(scene.polygonColors.get("RO"), "#6FA0D6", "participants are a muted step of the same stage colour");
  assert.equal(scene.polygonBorders.get("US-NM"), "#ffffff");
  for (const e of scene.colors.values()) assert.equal(e.hex, "#6FA0D6", "the side-list dot reads the same stage entry");
});

test("a different stage recolours that project only, and a leader change never changes the stage colour", () => {
  const staged = payload.map((p) => (p.project_id === "lu" ? { ...p, lifecycle: "PRODUCTION" } : p));
  const scene = buildCompanyScene(rowsFromPayload(staged), { stageOf });
  assert.deepEqual([...scene.stageCounts].sort(), [["evaluation", 3], ["production", 1]]);
  assert.ok(scene.points.filter((p) => p.projectId === "lu").every((p) => p.color === "#E8C273"));
  assert.ok(scene.points.filter((p) => p.projectId !== "lu").every((p) => p.color === "#6FA0D6"));
  const swapped = staged.map((p) => (p.project_id === "lu" ? { ...p, leading: { structure: { classification: "HYBRID_ANCHOR_COMPONENT", participants: ["MU", "IN"], primary_jurisdiction: "MU", component_allocations: [comp("principal_production", "MU"), comp("post_vfx_package", "IN")] } } } : p));
  const after = buildCompanyScene(rowsFromPayload(swapped), { stageOf });
  assert.ok(after.points.filter((p) => p.projectId === "lu").every((p) => p.color === "#E8C273"), "still the Production gold");
});

test("the stage legend lists stages, never productions, and comes from the existing PROJECT_STATUSES", () => {
  const src = readFileSync(join(SRC, "screens/company/CompanyGlobe.jsx"), "utf8");
  assert.match(src, /ACTIVE_STAGES\.map/);
  assert.doesNotMatch(src, /scene\.legend|portfolioPalette/);
  const stage = readFileSync(join(SRC, "lib/companyStage.js"), "utf8");
  assert.match(stage, /PROJECT_STATUSES/);
  assert.match(stage, /archived/, "archived is excluded from the active-stage legend");
  assert.doesNotMatch(readFileSync(join(SRC, "lib/companyScene.js"), "utf8"), /hash|assignProjectColors|PALETTE/i);
});

test("replacing one project's leader replaces ONLY that project's geography; nothing stale is kept", () => {
  const before = buildCompanyScene(rowsFromPayload(payload), { stageOf });
  const swapped = payload.map((p) => (p.project_id === "lu"
    ? { ...p, leading: { structure: { classification: "HYBRID_ANCHOR_COMPONENT", participants: ["MU", "IN"], primary_jurisdiction: "MU", component_allocations: [comp("principal_production", "MU"), comp("post_vfx_package", "IN")] } } }
    : p));
  const after = buildCompanyScene(rowsFromPayload(swapped), { stageOf });
  assert.ok(before.polygonColors.has("ZA") && !after.polygonColors.has("ZA"), "the old participant territory is gone");
  assert.ok(!before.polygonColors.has("IN") && after.polygonColors.has("IN"), "the new participant territory appears");
  assert.deepEqual(after.points.filter((p) => p.projectId === "lu").map((p) => p.code), ["MU", "IN"]);
  assert.deepEqual(after.arcs.filter((a) => a.endCode === "ZA"), [], "no stale route");
  assert.equal(after.arcs.filter((a) => a.endCode === "IN").length, 1);
  for (const id of ["bh", "fvd", "lls"]) {
    assert.deepEqual(after.points.filter((p) => p.projectId === id), before.points.filter((p) => p.projectId === id), `${id} unchanged`);
  }
  assert.equal(after.arcs.length, before.arcs.length, "route count does not accumulate");
  // the live store override (an in-app Set as Leading) takes the same path
  const override = (id) => (id === "lu" ? { structure: swapped[3].leading.structure, selectionKnown: true, userSelected: true } : null);
  const rows = portfolioRows({ projects: payload }, override);
  assert.deepEqual(rows[3].structure.participants, ["MU", "IN"]);
  assert.deepEqual(rows[0].structure.participants, ["US-NM"]);
  assert.equal(resolvePortfolioRow(payload[3]).structure.participants[1], "ZA");
});

test("sidebar portfolio overlay: every active project in its stage colour from the same rows, principal marked, routes carried", () => {
  const rows = rowsFromPayload(payload);
  const o = buildPortfolioMiniOverlay(rows, stageOf);
  assert.equal(new Set(o.markers.map((m) => m.projectId)).size, 4);
  assert.ok(o.markers.every((m) => m.color === "#6FA0D6"), "mini-globe colour = Company Globe stage colour");
  assert.equal(o.markers.filter((m) => m.principal).length, 4);
  assert.equal(o.routes.length, 2);
  assert.ok(o.focus && o.portfolio);
  assert.equal(buildPortfolioMiniOverlay([], stageOf), null);
  const changed = buildPortfolioMiniOverlay(rowsFromPayload(payload.map((p) => (p.project_id === "lu" ? { ...p, leading: { structure: { ...p.leading.structure, participants: ["MU", "IN"], component_allocations: [comp("principal_production", "MU"), comp("post_vfx_package", "IN")] } } } : p))), stageOf);
  assert.notEqual(changed.key, o.key, "a changed leader changes the overlay key, so the mini-globe rebuilds");
});
