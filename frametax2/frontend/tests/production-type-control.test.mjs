// Production type control (Overview): the producer's stated type is a saved fact that changes program eligibility (backend: test_production_type_election_controls.py). Source-scan
// contracts in the style of this directory: one API call, one shared component, options and disclosure from the served view, the shared single-flight evaluation, no fabricated default.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const strip = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

test("the API client posts the stated type (null = not stated) to the project route and does not evaluate", () => {
  const api = strip(read("api.js"));
  assert.match(api, /export const postProductionType = \(projectId, format\) =>\s*request\(`\/projects\/\$\{projectId\}\/production-type`, \{ method: "POST", body: JSON\.stringify\(\{ format \}\) \}\);/);
});

test("the control takes its options, labels, state and disclosure from the served view and hard-codes no production type", () => {
  const src = strip(read("components/ProductionTypeLine.jsx"));
  assert.match(src, /productionType\.options\.map\(\(o\) => \(/);
  assert.match(src, /productionType\.state === "STATED"/);
  assert.match(src, /\{productionType\.note\}/);
  assert.doesNotMatch(src, /["'`](feature|series|documentary|animation)["'`]/i, "no production type literal: the served options are the only vocabulary");
  assert.doesNotMatch(src, /Feature film|TV series|Documentary|Animation/);
});

test("unknown stays selectable and is saved as null, never as a default", () => {
  const src = strip(read("components/ProductionTypeLine.jsx"));
  assert.match(src, /<option value="">— not stated<\/option>/);
  assert.match(src, /const format = e\.target\.value === "" \? null : e\.target\.value;/);
  assert.match(src, /productionType\.format \?\? ""/);
});

test("a choice saves the type then runs the shared single-flight evaluation; the control locks while a run is active; retained results start no silent run", () => {
  const src = strip(read("components/ProductionTypeLine.jsx"));
  assert.match(src, /await postProductionType\(projectId, format\);\s*if \(evaluateOnSave\) await runEvaluation\(projectId\);\s*else setSavedNotEvaluated\(true\);/);
  assert.match(src, /disabled=\{saving \|\| run\.running\}/);
  assert.match(src, /if \(saving \|\| run\.running\) return;/);
  assert.match(src, /<EvaluationStatus projectId=\{projectId\} onCompleted=\{onSaved\} compact \/>/);
  assert.match(src, /\{savedNotEvaluated && <RetainedSaveNote \/>\}/);
  assert.match(src, /role="alert" data-production-type-error="true"/);
});

test("the Overview mounts it in the Production facts column, refetching every mounted state hook (the identity header included), with the retained-results guard", () => {
  const src = strip(read("screens/production/Overview.jsx"));
  assert.match(src, /import ProductionTypeLine from "\.\.\/\.\.\/components\/ProductionTypeLine";/);
  assert.match(src, /<ProductionTypeLine\s+projectId=\{projectId\}\s+productionType=\{production\?\.production_type\}\s+onSaved=\{\(\) => \{ refetch\(\); window\.dispatchEvent\(new Event\("cineglobe:refetch"\)\); \}\}\s+evaluateOnSave=\{production\?\.evaluation_freshness !== "STALE"\}\s*\/>/);
});

test("the identity header shows the STATED production type from the served view, never a hard-coded 'Feature Film'", async () => {
  const hero = strip(read("components/ProductionHero.jsx"));
  assert.doesNotMatch(hero, /Feature Film/);
  assert.match(hero, /import \{ productionTypeLabel \} from "\.\.\/lib\/productionType";/);
  assert.match(hero, /\{productionTypeLabel\(production\?\.production_type\) \?\? "—"\}/);
  const { productionTypeLabel } = await import("../src/lib/productionType.js");
  const view = { state: "STATED", format: "documentary", options: [{ format: "feature", label: "Feature film" }, { format: "documentary", label: "Documentary" }] };
  assert.equal(productionTypeLabel(view), "Documentary");
  assert.equal(productionTypeLabel({ ...view, state: "NOT_STATED", format: null }), "Production type not stated");
  assert.equal(productionTypeLabel(undefined), null);
  assert.equal(productionTypeLabel({ ...view, format: "series" }), "series", "an unlisted stated format is shown as stored, never replaced by a default");
});
