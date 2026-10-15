// Filming locations, budget-line inputs and the persisted structure facts (NA-RECONCILIATION-24). Backend path: test_na_locality_*, test_na_line_inputs_controls.py, test_na_persisted_resolved_facts_controls.py.
// Pure-logic checks run the real modules; component contracts are source scans in the style of this directory (no DOM harness).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  blankDraft, consequencesFor, derivedRows, draftFromLocation, draftsFrom, effectiveDrafts, hasErrors, isDirty, jurisdictionOf, jurisdictionsOf, payloadFrom, resetProducerClassifications, suppliedRows,
  usedDays, validateDrafts,
} from "../src/lib/locations.js";
import { changedLineInputs, draftFromView, fieldKey, isLineDirty, personSummary, portionKey, validateLineDrafts } from "../src/lib/lineInputs.js";
import { relevantFacts, sectionsFor, structureLadder } from "../src/lib/resolvedRequirements.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");
const strip = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/.*$/gm, "$1");

const persisted = (over = {}) => ({ id: "a", label: "Set A", jurisdiction_code: "US-MO", role: "SELECTED", city: "Columbia", county: "Boone", days: 12, attributes: {}, evidence: {}, classifications: {
  county_class: { value: "1", source: "Missouri Association of Counties", method: "DATASET_LOOKUP", version: "2025-05" } }, unresolved: { rural_or_blighted: "Department of Economic Development determination" }, states: {}, ...over });
const view = (locs = [persisted()], extra = {}) => ({ locations: locs, total_days: 20, used_days: 12, pricing_effects: [], ...extra });

test("a program slug maps to its jurisdiction and only classifiable jurisdictions are offered", () => {
  assert.equal(jurisdictionOf("us_mo_motion_media_production_tax_credit"), "US-MO");
  assert.equal(jurisdictionOf("ca_bc_film_tv_tax_credit"), "CA-BC");
  assert.deepEqual(jurisdictionsOf(["us_mo_motion_media_production_tax_credit", "ca_federal_cptc", "us_tx_miip"]), ["US-MO"], "irrelevant jurisdictions are never asked about");
});

test("blank days are Unknown, zero is a real zero, and the two are different in the payload", () => {
  const unknown = draftFromLocation(persisted({ days: null }));
  const zero = draftFromLocation(persisted({ days: 0 }));
  assert.equal(unknown.days, "");
  assert.equal(zero.days, "0");
  assert.equal(payloadFrom([unknown])[0].days, null);
  assert.equal(payloadFrom([zero])[0].days, 0);
  assert.equal(usedDays([unknown]), 0);
});

test("location days cannot exceed the shoot total, and a same-place duplicate is refused", () => {
  const a = { ...draftFromLocation(persisted()), days: "12" };
  assert.equal(hasErrors(validateDrafts([a], 20)), false);
  assert.equal(hasErrors(validateDrafts([{ ...a, days: "20" }], 20)), false, "exactly the total is allowed");
  assert.match(validateDrafts([{ ...a, days: "21" }], 20)._all.days, /more than the shoot total of 20/);
  const dup = { ...a, id: "b", label: "set a" };
  assert.match(validateDrafts([a, dup], null).b.label, /counted twice/);
  assert.equal(hasErrors(validateDrafts([a, { ...a, id: "c", label: "Set B" }], null)), false, "two sets in one city are two locations");
  assert.deepEqual(validateDrafts([{ ...a, days: "1.5" }], null).a.days, "Whole days between 0 and 2000");
});

test("a selected planning location supersedes the retained schedule of the same jurisdiction so days are not counted twice", () => {
  const sched = { ...draftFromLocation(persisted({ id: "s", role: "SCHEDULE", label: "Old", days: 10 })) };
  const sel = { ...draftFromLocation(persisted({ id: "p", role: "SELECTED", label: "New", days: 12 })) };
  const other = { ...draftFromLocation(persisted({ id: "o", role: "SCHEDULE", jurisdiction_code: "CA-MB", label: "Home", days: 8 })) };
  assert.deepEqual(effectiveDrafts([sched, sel, other]).map((d) => d.id), ["p", "o"]);
  assert.equal(usedDays([sched, sel, other]), 20);
});

test("a classification the producer supplies needs its source, and what is sent carries method, confidence and date", () => {
  const d = { ...blankDraft("US-MO"), id: "x", label: "Farm set", county: "Cole", days: "5", attrs: { rural_or_blighted: "yes" } };
  assert.match(validateDrafts([d], null).x.source, /Name the source/);
  const ok = { ...d, source: "DED determination letter", method: "AUTHORITY_DETERMINATION", confidence: "AUTHORITATIVE", effective_date: "2026-09-01" };
  assert.equal(hasErrors(validateDrafts([ok], null)), false);
  assert.deepEqual(payloadFrom([ok])[0].attributes, { rural_or_blighted: true });
  assert.deepEqual(payloadFrom([ok])[0].evidence.rural_or_blighted, { source: "DED determination letter", method: "AUTHORITY_DETERMINATION", confidence: "AUTHORITATIVE", effective_date: "2026-09-01" });
  const no = { ...ok, attrs: { rural_or_blighted: "no" } };
  assert.deepEqual(payloadFrom([no])[0].attributes, { rural_or_blighted: false }, "a verified non-qualifying location is stored as No, distinct from Unknown");
  const unknown = { ...ok, attrs: { rural_or_blighted: "" } };
  assert.deepEqual(payloadFrom([unknown])[0].attributes, {}, "Unknown sends nothing");
  assert.deepEqual(validateDrafts([{ ...ok, jurisdiction_code: "CA-NS", attrs: { ns_distance_km: "ten" } }], null).x.ns_distance_km, "Enter a number");
});

test("derived classifications and producer-supplied ones are separate, read-only rows with provenance", () => {
  const l = persisted({ attributes: { rural_or_blighted: true }, evidence: { rural_or_blighted: { source: "DED letter", method: "PRODUCER_ASSERTED", confidence: "STATED" } },
    classifications: { county_class: { value: "1", source: "Missouri Association of Counties", method: "DATASET_LOOKUP", version: "2025-05" }, mo_rural_or_blighted: { value: true, source: "DED letter", method: "PRODUCER_ASSERTED", confidence: "STATED" } } });
  assert.deepEqual(derivedRows(l).map((r) => r.key), ["county_class"]);
  assert.deepEqual(suppliedRows(l).map((r) => r.key), ["mo_rural_or_blighted"]);
});

test("cancel restores the persisted list, reset clears one location's producer classifications, an unchanged list is not dirty", () => {
  const v = view([persisted({ attributes: { rural_or_blighted: true }, evidence: { rural_or_blighted: { source: "s", method: "PRODUCER_ASSERTED", confidence: "STATED" } } })]);
  const drafts = draftsFrom(v);
  assert.equal(isDirty(drafts, v), false, "an unchanged save is not a change");
  const edited = drafts.map((d) => ({ ...d, days: "13" }));
  assert.equal(isDirty(edited, v), true);
  assert.equal(isDirty(draftsFrom(v), v), false, "cancel = draftsFrom(view)");
  const reset = resetProducerClassifications(drafts[0]);
  assert.deepEqual(payloadFrom([reset])[0].attributes, {});
  assert.equal(isDirty([reset], v), true);
  assert.deepEqual(effectiveDrafts([]).length, 0);
});

test("the pricing consequence is limited to the selected programs", () => {
  const v = view([], { pricing_effects: [
    { predicate: "mo_rural_or_blighted", label: "rural", state: "UNKNOWN", effects: [{ program: "us_mo_x", text: "+5 points on the base rate" }] },
    { predicate: "bc_distant", label: "distant", state: "MET", effects: [{ program: "ca_bc_x", text: "distant location (6%)" }] }] });
  assert.deepEqual(consequencesFor(v, ["us_mo_x"]).map((c) => c.predicate), ["mo_rural_or_blighted"]);
});

// ── budget-line inputs ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
const lineView = () => ({ lines: [{ line_id: "L1", description: "Crew", category: "btl_resident_labor", amount_usd: 500000, fields: [
  { name: "payee_id", label: "Person", kind: "text", choices: [], value: null, state: "UNKNOWN" },
  { name: "payee_compensation_complete", label: "Whole compensation", kind: "boolean", choices: [], value: null, state: "UNKNOWN" },
  { name: "mt_tax_withheld", label: "Withheld", kind: "boolean", choices: [], value: false, state: "STATED" },
  { name: "assistance_usd", label: "Assistance", kind: "number", choices: [], value: 0, state: "STATED", max_usd: 500000 }],
  portions: [{ program: "us_ar_x", uplift: "addons", amount_usd: null }] }], persons: [{ payee: "Pat", lines: ["L1"], total_usd: 500000, complete: true }] });

test("Unknown is not No and zero is not Unknown in the line picker", () => {
  const v = lineView();
  const d = draftFromView(v);
  assert.equal(d[fieldKey("L1", "mt_tax_withheld")], "no");
  assert.equal(d[fieldKey("L1", "payee_compensation_complete")], "");
  assert.equal(d[fieldKey("L1", "assistance_usd")], "0");
  assert.equal(isLineDirty(v, d), false);
  const cleared = { ...d, [fieldKey("L1", "mt_tax_withheld")]: "", [fieldKey("L1", "assistance_usd")]: "" };
  assert.deepEqual(changedLineInputs(v, cleared).line_facts, [{ line_id: "L1", field: "mt_tax_withheld", value: null }, { line_id: "L1", field: "assistance_usd", value: null }], "clearing resets to Unknown (null)");
  const yes = { ...d, [fieldKey("L1", "mt_tax_withheld")]: "yes" };
  assert.deepEqual(changedLineInputs(v, yes).line_facts, [{ line_id: "L1", field: "mt_tax_withheld", value: true }]);
});

test("a qualifying portion and a line amount cannot exceed the line; a complete-compensation claim needs a person", () => {
  const v = lineView();
  const d = draftFromView(v);
  assert.deepEqual(validateLineDrafts(v, { ...d, [portionKey("L1", "us_ar_x", "addons")]: "500000" }), {});
  assert.match(validateLineDrafts(v, { ...d, [portionKey("L1", "us_ar_x", "addons")]: "500000.01" })[portionKey("L1", "us_ar_x", "addons")], /cannot exceed the line amount/);
  assert.match(validateLineDrafts(v, { ...d, [fieldKey("L1", "assistance_usd")]: "500001" })[fieldKey("L1", "assistance_usd")], /Cannot exceed the line amount/);
  assert.match(validateLineDrafts(v, { ...d, [fieldKey("L1", "payee_compensation_complete")]: "yes" })[fieldKey("L1", "payee_compensation_complete")], /Identify the person/);
  assert.deepEqual(validateLineDrafts(v, { ...d, [fieldKey("L1", "payee_id")]: "Pat", [fieldKey("L1", "payee_compensation_complete")]: "yes" }), {});
  assert.deepEqual(changedLineInputs(v, { ...d, [portionKey("L1", "us_ar_x", "addons")]: "120000" }).uplift_basis, [{ program: "us_ar_x", uplift: "addons", line_id: "L1", amount_usd: 120000 }]);
  assert.equal(personSummary(v)[0].text, "Pat: 1 line(s), 500,000 USD");
});

// ── persisted structure facts ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
test("the facts the generation actually used override the project view: derived are read-only with provenance, Unknown keeps its effect", () => {
  const fact = (key, state, over = {}) => ({ key, label: key, kind: "boolean", state, value: null, provenance: "UNKNOWN", editable: true, category: "CONDITIONAL_UPSIDE", programs: ["us_mo"], effects: [], ...over });
  const v = { groups: [{ id: "mo", title: "Missouri", programs: ["us_mo"], facts: [fact("mo_a", "UNKNOWN"), fact("mo_b", "UNKNOWN")] }] };
  const structure = { program_slugs: ["us_mo"], resolved_facts: [
    { fact_key: "mo_a", state: "TRUE", value: true, provenance: "SCENARIO_ASSUMED", basis: "all principal photography in US-MO", effect: "+5 points on the base rate", scope: { program: "us_mo" } },
    { fact_key: "mo_b", state: "UNKNOWN", value: null, provenance: "UNKNOWN", effect: "+2 points on the base rate", scope: { program: "us_mo" } },
    { fact_key: "ca_x_days_in_x", state: "VALUE", value: 40, provenance: "SCENARIO_ASSUMED", basis: "40 of 40 days", effect: null, scope: { program: "us_mo" } }] };
  const facts = Object.fromEntries(relevantFacts(v, structure).map((f) => [f.key, f]));
  assert.equal(facts.mo_a.provenance, "SCENARIO_ASSUMED");
  assert.equal(facts.mo_a.editable, false);
  assert.equal(facts.mo_a.category, "SATISFIED");
  assert.equal(facts.mo_b.editable, true, "an Unknown stays a producer question");
  assert.deepEqual(facts.mo_b.effects, ["+2 points on the base rate"]);
  assert.equal(facts.ca_x_days_in_x.editable, false, "a persisted record the catalog does not list is a read-only row");
  const sections = sectionsFor(v, structure);
  assert.deepEqual(sections.satisfied.map((f) => f.key).sort(), ["ca_x_days_in_x", "mo_a"]);
});

// ── component contracts ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
test("the locations section saves once through the shared flow, offers only the selected structure's jurisdictions and locks while running", () => {
  const src = strip(read("components/ShootLocationsSection.jsx"));
  assert.match(src, /const saved = await postShootLocations\(projectId, payloadFrom\(drafts\)\);/);
  assert.match(src, /if \(evaluateOnSave\) await runEvaluation\(projectId\);\s*else setSavedNotEvaluated\(true\);/);
  assert.equal((src.match(/runEvaluation\(projectId\)/g) || []).length, 1);
  assert.match(src, /const jurisdictions = jurisdictionsOf\(programs\);/);
  assert.match(src, /if \(!projectId \|\| !shown \|\| !jurisdictions\.length\) return null;/);
  assert.match(src, /const locked = saving \|\| run\.running;/);
  assert.match(src, /disabled=\{!dirty \|\| hasErrors\(errors\) \|\| locked\}/);
  assert.match(src, /setDrafts\(draftsFrom\(shown\)\)/, "cancel restores the persisted list");
  assert.match(src, /resetProducerClassifications\(d\)/);
  assert.match(src, /data-derived-classification=\{r\.key\}/);
  assert.match(src, /data-supplied-classification=\{r\.key\}/);
  assert.match(src, /<option value="">Unknown<\/option>/);
  assert.match(src, /useEffect\(\(\) => \{ setShown\(view\); setDrafts\(draftsFrom\(view\)\); \}, \[view\]\);/, "a cold reload restores the persisted list");
  assert.doesNotMatch(src, /us_mo_|ca_bc_|ca_ns_/, "no program is hard-coded in the component");
});

test("the line section reads the picker (never evaluating), saves only what changed through the one writer, and is part of the panel", () => {
  const src = strip(read("components/LineInputsSection.jsx"));
  assert.match(src, /await postProgramFacts\(projectId, \{ line_facts, uplift_basis \}\);/);
  assert.equal((src.match(/runEvaluation\(projectId\)/g) || []).length, 1);
  assert.match(src, /getLineInputs\(projectId, programKey\.split\(","\)\)/);
  assert.doesNotMatch(src, /useEffect\([^)]*postProgramFacts|useEffect\([^)]*runEvaluation/s);
  assert.match(src, /\(derived, read-only\)/);
  const panel = strip(read("components/ResolvedRequirementsPanel.jsx"));
  assert.match(panel, /<ShootLocationsSection projectId=\{projectId\} view=\{shootLocations\} structure=\{structure\}/);
  assert.match(panel, /<LineInputsSection projectId=\{projectId\} structure=\{structure\}/);
  const api = strip(read("api.js"));
  assert.match(api, /export const getShootLocations = \(projectId\) => request\(`\/projects\/\$\{projectId\}\/shoot-locations`\);/);
  assert.match(api, /export const postShootLocations = \(projectId, locations\) => request\(`\/projects\/\$\{projectId\}\/shoot-locations`, \{ method: "POST", body: JSON\.stringify\(\{ locations \}\) \}\);/);
});

test("the Missouri ladder follows the facts the generation used: a full-relocation scenario earns the filming points", () => {
  const ladder = { base_pct: 20, max_pct: 42, confirmed_pct: 20, potential_pct: 42, steps: [{ id: "filmed", fact_key: "mo_a", points: 5, state: "UNKNOWN" }, { id: "rural", fact_key: "mo_b", points: 5, state: "UNKNOWN" }, { id: "county", fact_key: "mo_c", points: 2, state: "UNKNOWN" }] };
  const fact = (key) => ({ key, label: key, kind: "boolean", state: "UNKNOWN", value: null, provenance: "UNKNOWN", editable: true, category: "CONDITIONAL_UPSIDE", programs: ["us_mo_motion_media_production_tax_credit"], effects: [] });
  const v = { missouri: ladder, groups: [{ id: "g", title: "MO", programs: ["us_mo_motion_media_production_tax_credit"], facts: [fact("mo_a"), fact("mo_b"), fact("mo_c")] }] };
  const structure = { program_slugs: ["us_mo_motion_media_production_tax_credit"], resolved_facts: [
    { fact_key: "mo_a", state: "TRUE", value: true, provenance: "SCENARIO_ASSUMED", scope: {} }, { fact_key: "mo_b", state: "FALSE", value: false, provenance: "PRODUCER_STATED", scope: {} }] };
  const l = structureLadder(v, structure);
  assert.deepEqual([l.confirmed_pct, l.potential_pct], [25, 27], "20 + 5 filming confirmed; rural refuted; county still Unknown: 25 + 2");
  assert.deepEqual(l.steps.map((s) => s.state), ["TRUE", "FALSE", "UNKNOWN"]);
  assert.equal(structureLadder({ groups: [] }, structure), null);
});
