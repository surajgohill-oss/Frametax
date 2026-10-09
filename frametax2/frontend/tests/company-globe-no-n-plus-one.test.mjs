import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { resolveLeadingStructure } from "../src/lib/leadingResolve.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

test("Company Globe and the sidebar read ONE aggregate payload: no per-project /state, no project list, no org lookup", () => {
  const company = read("screens/company/CompanyGlobe.jsx");
  for (const forbidden of [/getProjectState/, /getProjects\b/, /getCurrentOrganization/, /Promise\.all/, /useCineGlobe/]) {
    assert.doesNotMatch(company, forbidden);
  }
  assert.match(company, /loadPortfolio\(/);
  assert.match(read("shell/Sidebar.jsx"), /loadPortfolio\(\)/);
  const store = read("lib/leadingSelection.js");
  assert.match(store, /getPortfolioGlobe\(\)/);
  assert.equal((store.match(/getPortfolioGlobe\(/g) || []).length, 1, "the portfolio is requested from one place only");
  assert.match(read("api.js"), /_portfolioInFlight \|\|=/, "concurrent callers share one in-flight request");
});

test("leading rule: explicit Set as Leading, else the anchor; canonical and leading-conditional structures are never substituted", () => {
  const structures = [{ structure_id: "a" }, { structure_id: "b" }, { structure_id: "c" }];
  const allocated = { structures, canonical_selected_structure_id: null, leading_conditional_structure: { structure_id: "b" } };
  assert.deepEqual(resolveLeadingStructure(allocated, "c"), { structure: structures[2], source: "user" });
  assert.deepEqual(resolveLeadingStructure(allocated, null), { structure: null, source: "baseline" }, "a served leading-conditional structure is not drawn unprompted");
  assert.deepEqual(resolveLeadingStructure({ ...allocated, canonical_selected_structure_id: "a" }, null), { structure: null, source: "baseline" }, "nor the canonical selection");
  const pool = { ...allocated, optimizer_candidates: [{ structure_id: "multi", participants: ["X", "Y", "Z"] }] };
  assert.equal(resolveLeadingStructure(pool, "multi").structure.participants.length, 3, "a choice from the optimizer pool resolves");
  assert.deepEqual(resolveLeadingStructure(allocated, "gone"), { structure: null, source: "baseline" }, "a vanished choice returns to the anchor, never remaps");
  assert.deepEqual(resolveLeadingStructure(allocated, undefined), { structure: null, source: "baseline" }, "clearing the choice returns to the anchor");
});
