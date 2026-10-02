import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { alternativeLabel, fitTag, ALT } from "../src/lib/alternativeLabels.js";
import { optimizerProjection } from "../src/lib/workspaceScenarioMode.js";

const read = (p) => readFileSync(new URL(p, import.meta.url), "utf8");
const s = (id, extra = {}) => ({ structure_id: id, candidate_status: "PRICED", ...extra });

test("served fit drives the label: weak and unknown stay visible as references, confirmed unchanged", () => {
  assert.equal(alternativeLabel(s("a", { recommendation_status: "EVALUATED_ALTERNATIVE", savings_vs_current_usd: 50_000, production_fit_status: "WEAK" })), ALT.LOW_FIT);
  assert.equal(alternativeLabel(s("b", { recommendation_status: "EVALUATED_ALTERNATIVE", savings_vs_current_usd: 50_000, production_fit_status: "UNKNOWN" })), ALT.FIT_UNCONFIRMED);
  assert.equal(alternativeLabel(s("c", { recommendation_status: "EVALUATED_ALTERNATIVE", savings_vs_current_usd: 50_000, production_fit_status: "WORKABLE" })), ALT.COST_SAVING);
  assert.equal(ALT.FIT_UNCONFIRMED, "LOCATION FIT UNCONFIRMED");
  assert.equal(alternativeLabel(s("d", { recommendation_status: "RECOMMENDED", production_fit_status: "STRONG" }), "d"), ALT.LEADING);
  // legal rejection stays UNAVAILABLE whatever the fit says
  assert.equal(alternativeLabel({ candidate_status: "RULE_REJECTED", production_fit_status: "STRONG" }), ALT.UNAVAILABLE);
  assert.equal(fitTag({ production_fit_status: "WEAK" }), " · low location fit");
  assert.equal(fitTag({ production_fit_status: "STRONG" }), "");
});

test("evaluated alternatives are ordered by the SERVED fit_priority first; no scenario is dropped", () => {
  const evaluated = [
    s("weak", { recommendation_status: "EVALUATED_ALTERNATIVE", fit_priority: 4, savings_vs_current_usd: 900_000 }),
    s("unk", { recommendation_status: "EVALUATED_ALTERNATIVE", fit_priority: 3, savings_vs_current_usd: 800_000 }),
    s("ok-low", { recommendation_status: "COSTS_MORE", fit_priority: 2, savings_vs_current_usd: -5 }),
    s("ok", { recommendation_status: "EVALUATED_ALTERNATIVE", fit_priority: 2, savings_vs_current_usd: 10 }),
  ];
  const proj = optimizerProjection({ evaluated_optimizer_alternatives: evaluated, recommended_optimizer_options: [] });
  assert.deepEqual(proj.evaluated.map((e) => e.structure_id), ["ok", "ok-low", "unk", "weak"]);
  assert.equal(proj.evaluated.length, 4);
});

test("React renders served fit only: no fit classifier in the frontend", () => {
  for (const f of ["../src/lib/alternativeLabels.js", "../src/lib/workspaceScenarioMode.js", "../src/shell/Inspector.jsx"]) {
    const src = read(f);
    assert.ok(!/jurisdiction_capability_profile|match_capability|feasibility_discovery/.test(src), f);
  }
  const inspector = read("../src/shell/Inspector.jsx");
  assert.match(inspector, /Production fit/);
  assert.match(inspector, /production_fit_legs/);
  assert.match(inspector, /production_fit_reasons/);
});

test("location controls: project-scoped endpoint, never the legacy singleton, and exposed on Overview", () => {
  const api = read("../src/api.js");
  assert.match(api, /postProjectLocations = \(projectId, overrides\) =>\s*request\(`\/projects\/\$\{projectId\}\/locations`/);
  const details = read("../src/components/ProductionDetails.jsx");
  assert.match(details, /if \(projectId\) await postProjectLocations\(projectId, locs\)/);
  assert.match(details, /never remove a\s+jurisdiction|never remove a jurisdiction/);
  const overview = read("../src/screens/production/Overview.jsx");
  assert.ok(!/showLocationRequirements=\{false\}/.test(overview));
});

test("Workspace counters, dropdown order and Globe list read the same served fit fields", () => {
  const ws = read("../src/screens/production/Workspace.jsx");
  assert.match(ws, /optimizer_production_fit_counts/);
  assert.match(ws, /fit_priority \?\? 2\) - \(b\.structure\.fit_priority \?\? 2\)/);
  assert.match(ws, /fitTag\(s\)/);
  const globeData = read("../src/lib/globeData.js");
  assert.match(globeData, /production_fit_status: structure\.production_fit_status/);
  assert.match(read("../src/screens/production/ProjectGlobe.jsx"), /alternativeLabel\(s, /);
  assert.match(ws, /alternativeLabel\(structure, optimizerLeadingId\)/);
});
