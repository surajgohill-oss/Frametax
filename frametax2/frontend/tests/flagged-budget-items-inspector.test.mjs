// Flagged budget items in the Inspector (Overview account click and Workspace segment click): source value, unresolved reason,
// evidence needed and the ONE canonical producer control (the saved project contingency election). Source-scan contracts in the
// style of this directory; the behaviour of the saved election (save / reload / reset / bounds) is covered on the backend in
// test_contingency_planned_cost_controls.py. There is deliberately no generic eligibility override.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const strip = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

test("both Inspectors render flagged items through the one FlaggedItem block", () => {
  const src = strip(read("shell/Inspector.jsx"));
  assert.match(src, /function FlaggedItem\(/);
  assert.match(src, /isFlagged\(data\.state\) \? \(\s*<FlaggedItem item=\{data\} election=\{data\.contingencyElection\}/);
  assert.match(src, /const flaggedTrace = trace\.filter\(\(t\) => isFlagged\(t\.state\)\)/);
  assert.match(src, /<FlaggedItem key=\{`\$\{t\.line_id \|\| t\.account_code\}-\$\{i\}`\} item=\{t\} election=\{data\.contingencyElection\}/);
});

test("a flagged item shows source value, unresolved reason, evidence needed and states that nothing is eligible by default", () => {
  const src = strip(read("shell/Inspector.jsx"));
  for (const needle of ["<dt>Source value</dt>", "<dt>Unresolved because</dt>", "Evidence needed:", "never treated as eligible by default", "Saved producer input:"]) {
    assert.ok(src.includes(needle), `missing: ${needle}`);
  }
});

test("no blanket eligibility override: the Inspector adds no endpoint call beyond the shared contingency control", () => {
  const src = strip(read("shell/Inspector.jsx"));
  assert.doesNotMatch(src, /markEligible|setEligib|forceQualif|overrideQualif|eligibilityOverride/i);
  const imports = [...src.matchAll(/import \{([^}]*)\} from "\.\.\/api";/g)].map((m) => m[1].trim());
  // the one mutation is unchanged; the one added call is the read-only GET of a jurisdiction winner's omitted segment trace (never a write, never an evaluation)
  assert.deepEqual(imports, ["postProjectContentGates, getJurisdictionWinner"]);
  const api = strip(read("api.js"));
  assert.match(api, /export const getJurisdictionWinner = \(projectId, code\) =>\s*request\(`\/projects\/\$\{projectId\}\/evaluation\/jurisdiction-winner\/\$\{encodeURIComponent\(code\)\}`\);/, "a plain GET");
});

test("the contingency control is ONE shared component (rail and Inspector), saving the whitelisted fact then re-evaluating", () => {
  const rail = strip(read("components/BudgetRail.jsx"));
  const shared = strip(read("components/ContingencyElection.jsx"));
  assert.match(rail, /import \{ ContingencyLine \} from "\.\/ContingencyElection";/);
  assert.doesNotMatch(rail, /function ContingencyLine/);
  assert.match(shared, /export function ContingencyLine/);
  assert.match(shared, /postProjectAssumptions\(projectId, \{ contingency_expected_utilization_pct: pct \}\)/);
  assert.match(shared, /await beginEvaluation\(projectId\)/);
  assert.match(shared, /planning\?\.state === "ELECTED"/);                 // planned cost shown only for a real election
  assert.match(shared, /No utilization stated: planned cost = full budget/);
});

test("the saved election handed to the Inspector comes from the persisted fact, never local state", () => {
  const overview = strip(read("screens/production/Overview.jsx"));
  const workspace = strip(read("screens/production/Workspace.jsx"));
  assert.match(overview, /contingencyElection: \/contingen\/i\.test\(line\.label \|\| ""\) \? \{\s*projectId, currentPct: contingencyPct, planning: production\?\.contingency_planning/);
  assert.match(workspace, /facts\?\.answers\?\.contingency_expected_utilization_pct == null \? null : Number/);
  assert.equal((workspace.match(/contingencyByAccount, contingencyElection \}/g) || []).length, 2);
});
