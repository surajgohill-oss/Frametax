// Resolved requirements (NA-RECONCILIATION-22): Overview input -> validation -> the one POST -> the shared single-flight evaluation -> refreshed served view. Backend path: test_na_resolved_fact_layer_controls.py
// and test_program_fact_wiring_controls.py. Pure-logic checks run the real module; component contracts are source scans in the style of this directory (no DOM harness).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  booleanOptions, changedFacts, chooseBoolean, draftFrom, factStatusText, isDirty, isReadOnly, ladderLines, provenanceLabel, stillNeeded, validateDraft, validateFact,
} from "../src/lib/resolvedRequirements.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const strip = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

const num = (key, state = "UNKNOWN", value = null, extra = {}) => ({ key, kind: "number", state, value, min: 0, max: 2000, whole: true, provenance: state === "UNKNOWN" ? "UNKNOWN" : "PRODUCER_STATED", editable: true, ...extra });
const bool = (key, state = "UNKNOWN", extra = {}) => ({ key, kind: "boolean", state, value: state === "TRUE" ? true : state === "FALSE" ? false : null, provenance: state === "UNKNOWN" ? "UNKNOWN" : "PRODUCER_STATED", editable: true, ...extra });
const election = (key, state = "UNKNOWN", exclusive_with = null) => bool(key, state, { kind: "election", exclusive_with });
const derived = (key, value) => num(key, "VALUE", value, { provenance: "SCHEDULE_DERIVED", editable: false });
const group = { id: "g", facts: [num("days_in_bc", "VALUE", 40), num("days_out"), election("after_2024", "TRUE", "before_2025"), election("before_2025", "UNKNOWN", "after_2024"), bool("rural", "FALSE"),
  bool("hires"), num("payments_usd", "UNKNOWN", null, { whole: false, max: 1e9 }), derived("total_days", 38)] };

test("a draft restores stored values: Yes, No and Unknown are three different answers; a derived fact has no draft", () => {
  assert.deepEqual(draftFrom(group), { days_in_bc: "40", days_out: "", after_2024: "yes", before_2025: "", rural: "no", hires: "", payments_usd: "" });
  assert.equal("total_days" in draftFrom(group), false, "a schedule-derived fact is read-only: it is never part of the form");
});

test("only changed facts are sent; a predicate may be answered No, an election never is; blank clears to Unknown", () => {
  const draft = { ...draftFrom(group), days_out: "30", days_in_bc: "", rural: "yes", hires: "no", after_2024: "" };
  assert.deepEqual(changedFacts(group, draft), { evidenced: { rural: true, hires: false, after_2024: null }, amounts: { days_out: 30, days_in_bc: null } });
  assert.equal(isDirty(group, draftFrom(group)), false, "an untouched form sends nothing");
  const cleared = { ...draftFrom(group), rural: "" };
  assert.deepEqual(changedFacts(group, cleared).evidenced, { rural: null }, "clearing a stated No returns to Unknown, not to Yes");
  const electionNo = { ...draftFrom(group), before_2025: "no" };
  assert.deepEqual(changedFacts(group, electionNo).evidenced, {}, "an election between alternatives is never answered No");
  assert.deepEqual(booleanOptions(election("e")), ["", "yes"]);
  assert.deepEqual(booleanOptions(bool("b")), ["", "yes", "no"]);
});

test("stating one side of an election leaves its partner Unknown in the draft", () => {
  const stated = chooseBoolean(group, draftFrom(group), "before_2025", "yes");
  assert.deepEqual(changedFacts(group, stated).evidenced, { before_2025: true, after_2024: null });
});

test("a stated zero is a real value that differs from Unknown", () => {
  assert.deepEqual(changedFacts(group, { ...draftFrom(group), payments_usd: "0" }).amounts, { payments_usd: 0 });
  const zeroStated = { ...group, facts: group.facts.map((f) => (f.key === "payments_usd" ? { ...f, state: "VALUE", value: 0, provenance: "PRODUCER_STATED" } : f)) };
  assert.equal(draftFrom(zeroStated).payments_usd, "0");
  assert.equal(isDirty(zeroStated, draftFrom(zeroStated)), false);
});

test("validation follows the served bounds, whole-number rule and number syntax", () => {
  const f = num("days", "UNKNOWN", null, { min: 1, max: 2000 });
  assert.equal(validateFact(f, ""), null);
  assert.equal(validateFact(f, "0"), "Between 1 and 2000");
  assert.equal(validateFact(f, "2001"), "Between 1 and 2000");
  assert.equal(validateFact(f, "10.5"), "Whole numbers only");
  assert.equal(validateFact(f, "ten"), "Enter a number");
  assert.equal(validateFact(f, "2000"), null);
  assert.deepEqual(validateDraft(group, { ...draftFrom(group), days_out: "-1" }), { days_out: "Between 0 and 2000" });
});

test("the provenance labels keep verified evidence, producer statements, scenario assumptions and Unknown apart", () => {
  const labels = ["VERIFIED", "PRODUCER_STATED", "SCENARIO_ASSUMED", "SCHEDULE_DERIVED", "UNKNOWN"].map(provenanceLabel);
  assert.equal(new Set(labels).size, 5);
  assert.equal(provenanceLabel("something-new"), "Unknown", "an unrecognised provenance is never presented as established");
  assert.equal(isReadOnly(derived("x", 1)), true);
  assert.equal(factStatusText(bool("b", "FALSE")), "No");
  assert.equal(factStatusText(bool("b")), "Unknown");
});

test("still-needed lists only Unknown facts the producer can state, using the exact requirement text", () => {
  const view = { groups: [{ title: "T", facts: [bool("a", "UNKNOWN", { requirement: "At least 50% filmed in Missouri" }), bool("b", "FALSE"), derived("c", 3), num("d", "UNKNOWN", null, { label: "d" })] }] };
  assert.deepEqual(stillNeeded(view).map((n) => [n.key, n.requirement]), [["a", "At least 50% filmed in Missouri"], ["d", "d"]]);
});

test("the Missouri ladder reads base, increases and total; 15% is never rendered as 15 points", () => {
  const lines = ladderLines({ base_pct: 20, max_pct: 42, confirmed_pct: 25, potential_pct: 37, steps: [
    { id: "filmed_50pct_in_missouri", fact_key: "k1", points: 5, state: "TRUE" }, { id: "rural_or_blighted_15pct", fact_key: "k2", points: 5, state: "FALSE" },
    { id: "script", fact_key: "k3", points: 5, state: "UNKNOWN" }, { id: "county", fact_key: "k4", points: 2, state: "UNKNOWN" }] });
  assert.deepEqual(lines.map((l) => l.text), ["Base 20%", "+5 points", "+5 points", "+5 points", "+2 points", "Confirmed 25% · up to 37% · maximum 42%"]);
  assert.ok(!lines.some((l) => /15 points/.test(l.text)));
  assert.deepEqual(ladderLines(null), []);
});

test("the API client reads and posts the facts on the one program-facts route and does not evaluate", () => {
  const api = strip(read("api.js"));
  assert.match(api, /export const getProgramFacts = \(projectId\) => request\(`\/projects\/\$\{projectId\}\/program-facts`\);/);
  assert.match(api, /export const postProgramFacts = \(projectId, \{ evidenced = \{\}, amounts = \{\} \} = \{\}\) =>\s*request\(`\/projects\/\$\{projectId\}\/program-facts`, \{ method: "POST", body: JSON\.stringify\(\{ evidenced, amounts \}\) \}\);/);
});

test("the panel saves then runs the shared single-flight evaluation once; retained results start none; the control locks while running", () => {
  const src = strip(read("components/ResolvedRequirementsPanel.jsx"));
  assert.match(src, /const saved = await postProgramFacts\(projectId, \{ evidenced, amounts \}\);/);
  assert.match(src, /if \(evaluateOnSave\) await runEvaluation\(projectId\);\s*else setSavedNotEvaluated\(true\);/);
  assert.equal((src.match(/runEvaluation\(projectId\)/g) || []).length, 1, "exactly one evaluation call site");
  assert.match(src, /if \(savingGroup \|\| run\.running\) return;/);
  assert.match(src, /const locked = savingGroup !== null \|\| run\.running;/);
  assert.match(src, /\{savedNotEvaluated && <RetainedSaveNote \/>\}/);
  assert.match(src, /<EvaluationStatus projectId=\{projectId\} onCompleted=\{onSaved\} compact \/>/);
});

test("labels, groups, bounds, provenance and requirements come from the served view; derived facts are read-only; no fact key is named in the component", () => {
  const src = strip(read("components/ResolvedRequirementsPanel.jsx"));
  assert.match(src, /view\.groups\.map\(\(group\) =>/);
  assert.match(src, /data-provenance=\{f\.provenance\}/);
  assert.match(src, /data-read-only=\{isReadOnly\(f\) \? "true" : "false"\}/);
  assert.match(src, /isReadOnly\(f\) \? \(\s*<span className="pd-col-label rr-readonly"/, "a derived or assumed fact renders as text, not as a control");
  assert.match(src, /<option value="">Unknown<\/option>/);
  assert.match(src, /booleanOptions\(f\)\.includes\("no"\) && <option value="no">No<\/option>/, "No is offered for predicates only, never for an election");
  assert.match(src, /Needed: \{f\.requirement \?\? f\.label\}/);
  assert.match(src, /view\.missouri && \(/);
  assert.doesNotMatch(src, /ca_bc_|ca_ns_|ca_nb_|ca_sk_|us_mt_|us_mo_|mo_|ca_federal_/, "no fact key is named in the component");
  assert.match(src, /setView\(programFacts\); setDrafts\(\{\}\);/, "a refetch / cold reload restores the stored values");
});

test("provenance has distinct styling for verified, producer-stated, scenario-assumed and unknown facts", () => {
  const css = readFileSync(join(SRC, "styles", "screens.css"), "utf8");
  for (const cls of ["rr-prov-verified", "rr-prov-producer_stated", "rr-prov-scenario_assumed", "rr-prov-unknown"]) assert.match(css, new RegExp(`\\.${cls}`), cls);
});

test("the Overview mounts it in the Production facts column with the retained-results guard and the same refetch as the other producer inputs", () => {
  const src = strip(read("screens/production/Overview.jsx"));
  assert.match(src, /import ResolvedRequirementsPanel from "\.\.\/\.\.\/components\/ResolvedRequirementsPanel";/);
  assert.match(src, /<ResolvedRequirementsPanel\s+projectId=\{projectId\}\s+programFacts=\{production\?\.program_facts\}\s+onSaved=\{\(\) => \{ refetch\(\); window\.dispatchEvent\(new Event\("cineglobe:refetch"\)\); \}\}\s+evaluateOnSave=\{production\?\.evaluation_freshness !== "STALE"\}\s*\/>/);
  assert.doesNotMatch(src, /ProgramFactsPanel/, "the 73-question manual panel is gone");
});

test("opening a project never writes or evaluates program facts: the panel only reads the served view", () => {
  const src = strip(read("components/ResolvedRequirementsPanel.jsx"));
  assert.doesNotMatch(src, /useEffect\([^)]*postProgramFacts|useEffect\([^)]*runEvaluation/s);
  assert.match(src, /useEffect\(\(\) => \{ setView\(programFacts\); setDrafts\(\{\}\); \}, \[programFacts\]\);/);
});
