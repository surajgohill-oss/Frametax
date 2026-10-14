// Producer-stated program facts (NA-RECONCILIATION-21): Overview input -> validation -> the one POST -> the shared single-flight evaluation -> refreshed served view. Backend path: test_program_fact_wiring_controls.py.
// Pure-logic checks run the real form module; component contracts are source scans in the style of this directory (no DOM harness).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { changedFacts, chooseBoolean, draftFrom, isDirty, validateDraft, validateFact } from "../src/lib/programFacts.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const strip = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

const num = (key, state = "UNKNOWN", value = null, extra = {}) => ({ key, kind: "number", state, value, min: 0, max: 2000, whole: true, ...extra });
const bool = (key, state = "UNKNOWN", exclusive_with = null) => ({ key, kind: "boolean", state, value: state === "STATED" ? true : null, exclusive_with });
const group = { id: "g", facts: [num("days_in_bc", "STATED", 40), num("days_out"), bool("after_2024", "STATED", "before_2025"), bool("before_2025", "UNKNOWN", "after_2024"), num("payments_usd", "UNKNOWN", null, { whole: false, max: 1e9 })] };

test("a draft restores stored values and shows Unknown as blank, never zero or No", () => {
  assert.deepEqual(draftFrom(group), { days_in_bc: "40", days_out: "", after_2024: "yes", before_2025: "", payments_usd: "" });
});

test("only changed facts are sent; blank clears to null (Unknown); a boolean is true or null, never false", () => {
  const draft = { ...draftFrom(group), days_out: "30", days_in_bc: "", after_2024: "" };
  assert.deepEqual(changedFacts(group, draft), { evidenced: { after_2024: null }, amounts: { days_out: 30, days_in_bc: null } });
  assert.equal(isDirty(group, draftFrom(group)), false, "an untouched form sends nothing");
  const stated = chooseBoolean(group, draftFrom(group), "before_2025", true);
  assert.deepEqual(changedFacts(group, stated).evidenced, { before_2025: true, after_2024: null }, "stating one side leaves its exclusive partner Unknown");
  for (const payload of [changedFacts(group, stated), changedFacts(group, draft)]) assert.ok(!Object.values(payload.evidenced).includes(false), "a No is never sent");
});

test("a stated zero is a real value that differs from Unknown", () => {
  const draft = { ...draftFrom(group), payments_usd: "0" };
  assert.deepEqual(changedFacts(group, draft).amounts, { payments_usd: 0 });
  const zeroStated = { ...group, facts: group.facts.map((f) => (f.key === "payments_usd" ? { ...f, state: "STATED", value: 0 } : f)) };
  assert.equal(draftFrom(zeroStated).payments_usd, "0");
  assert.equal(isDirty(zeroStated, draftFrom(zeroStated)), false);
});

test("validation follows the served bounds, whole-number rule and number syntax", () => {
  const f = num("days", "UNKNOWN", null, { min: 1, max: 2000 });
  assert.equal(validateFact(f, ""), null, "blank is Unknown, allowed");
  assert.equal(validateFact(f, "0"), "Between 1 and 2000");
  assert.equal(validateFact(f, "2001"), "Between 1 and 2000");
  assert.equal(validateFact(f, "10.5"), "Whole numbers only");
  assert.equal(validateFact(f, "ten"), "Enter a number");
  assert.equal(validateFact(f, "1e3"), "Enter a number");
  assert.equal(validateFact(f, "2000"), null);
  assert.deepEqual(validateDraft(group, { ...draftFrom(group), days_out: "-1" }), { days_out: "Between 0 and 2000" });
});

test("the API client reads and posts the facts on the one program-facts route and does not evaluate", () => {
  const api = strip(read("api.js"));
  assert.match(api, /export const getProgramFacts = \(projectId\) => request\(`\/projects\/\$\{projectId\}\/program-facts`\);/);
  assert.match(api, /export const postProgramFacts = \(projectId, \{ evidenced = \{\}, amounts = \{\} \} = \{\}\) =>\s*request\(`\/projects\/\$\{projectId\}\/program-facts`, \{ method: "POST", body: JSON\.stringify\(\{ evidenced, amounts \}\) \}\);/);
});

test("the panel saves then runs the shared single-flight evaluation once; retained results start none; the control locks while running", () => {
  const src = strip(read("components/ProgramFactsPanel.jsx"));
  assert.match(src, /const saved = await postProgramFacts\(projectId, \{ evidenced, amounts \}\);/);
  assert.match(src, /if \(evaluateOnSave\) await runEvaluation\(projectId\);\s*else setSavedNotEvaluated\(true\);/);
  assert.equal((src.match(/runEvaluation\(projectId\)/g) || []).length, 1, "exactly one evaluation call site");
  assert.match(src, /if \(savingGroup \|\| run\.running\) return;/);
  assert.match(src, /disabled=\{savingGroup !== null \|\| run\.running\}/);
  assert.match(src, /\{savedNotEvaluated && <RetainedSaveNote \/>\}/);
  assert.match(src, /<EvaluationStatus projectId=\{projectId\} onCompleted=\{onSaved\} compact \/>/);
});

test("labels, groups, bounds and provenance come from the served view; no fact is hard-coded or defaulted; Unknown is offered", () => {
  const src = strip(read("components/ProgramFactsPanel.jsx"));
  assert.match(src, /view\.groups\.map\(\(group\) =>/);
  assert.match(src, /<option value="">Unknown<\/option>/);
  assert.match(src, /placeholder="Unknown"/);
  assert.match(src, /Producer-stated/);
  assert.doesNotMatch(src, /ca_bc_|ca_ns_|ca_nb_|ca_sk_|us_mt_|ca_federal_/, "no fact key is named in the component");
  assert.doesNotMatch(src, /<option value="no">|value="false"|=== false/, "a No is never offered");
  assert.match(src, /setView\(programFacts\); setDrafts\(\{\}\);/, "a refetch / cold reload restores the stored values");
});

test("the Overview mounts it in the Production facts column with the retained-results guard and the same refetch as the other producer inputs", () => {
  const src = strip(read("screens/production/Overview.jsx"));
  assert.match(src, /import ProgramFactsPanel from "\.\.\/\.\.\/components\/ProgramFactsPanel";/);
  assert.match(src, /<ProgramFactsPanel\s+projectId=\{projectId\}\s+programFacts=\{production\?\.program_facts\}\s+onSaved=\{\(\) => \{ refetch\(\); window\.dispatchEvent\(new Event\("cineglobe:refetch"\)\); \}\}\s+evaluateOnSave=\{production\?\.evaluation_freshness !== "STALE"\}\s*\/>/);
});

test("opening a project never writes or evaluates program facts: the panel only reads the served view", () => {
  const src = strip(read("components/ProgramFactsPanel.jsx"));
  assert.doesNotMatch(src, /useEffect\([^)]*postProgramFacts|useEffect\([^)]*runEvaluation/s);
  assert.match(src, /useEffect\(\(\) => \{ setView\(programFacts\); setDrafts\(\{\}\); \}, \[programFacts\]\);/);
});
