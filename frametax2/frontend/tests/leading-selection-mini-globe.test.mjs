import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { miniGlobeOverlay } from "../src/lib/globeStructure.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

test("mini-globe overlay: principal, participants and the structure's own routes; none without a structure", () => {
  const hybrid = {
    structure_id: "h", classification: "HYBRID_ANCHOR_COMPONENT", primary_jurisdiction: "GR", participants: ["GR", "RO"],
    component_allocations: [{ component: "principal_production", jurisdiction_code: "GR" }, { component: "post_vfx_package", jurisdiction_code: "RO" }],
  };
  const o = miniGlobeOverlay(hybrid);
  assert.deepEqual(o.markers.map((m) => [m.code, m.principal]), [["GR", true], ["RO", false]]);
  assert.equal(o.routes.length, 1);
  const single = miniGlobeOverlay({ structure_id: "s", classification: "SINGLE_JURISDICTION", primary_jurisdiction: "US-NM", participants: ["US-NM"] }, { homeCode: "US-NM" });
  assert.deepEqual(single.markers.map((m) => m.code), ["US-NM"]);
  assert.equal(single.routes.length, 0);
  assert.equal(miniGlobeOverlay(null), null);
});

test("Set as Leading goes through one project-scoped commit read by every Globe surface", () => {
  for (const path of ["screens/production/Workspace.jsx", "screens/production/Scenarios.jsx"]) {
    const src = read(path);
    assert.match(src, /commitLeadingStructure\(/, `${path} must commit through lib/leadingSelection.js`);
    assert.doesNotMatch(src, /patchProject\(projectId, \{ leading_structure_id/, `${path} must not write the selection on its own`);
  }
  assert.match(read("screens/company/CompanyGlobe.jsx"), /getLeadingSelection\(row\.project\.id\)/);
  assert.match(read("shell/Sidebar.jsx"), /useLeadingSelection\(projectId\)/);
  assert.match(read("lib/useCineGlobe.js"), /publishServedLeading\(projectId, data\)/);
});

test("the sidebar mini-globe pauses offscreen/hidden, honours reduced motion and keeps one renderer", () => {
  const src = read("components/CompactSidebarGlobe.jsx");
  assert.match(src, /IntersectionObserver/);
  assert.match(src, /visibilitychange/);
  assert.match(src, /prefers-reduced-motion: reduce/);
  assert.equal((src.match(/new THREE\.WebGLRenderer/g) || []).length, 1);
});
