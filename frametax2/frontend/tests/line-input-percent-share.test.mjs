// Percentage-of-line eligibility in the budget-line editor (NA_ALLOCATION_CALCULATION closeout). Backend path: test_na_allocation_calculation_closeout_controls.py.
// Pure logic runs the real module; the component contract is a source scan in the style of this directory (no DOM harness).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { changedLineInputs, draftFromView, fieldKey, isPercentField, percentAmount, percentNote, validateLineDrafts } from "../src/lib/lineInputs.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const read = (p) => readFileSync(join(SRC, p), "utf8");

const pct = (over = {}) => ({ name: "canadian_resident_share_pct", label: "Eligible share of this line: paid to Canadian-resident individuals", kind: "number", choices: [], consumer: "Federal PSTC labour basis", max_usd: null, max_value: 100, unit: "percent_of_line", value: null, state: "ASSUMED", assumed_pct: 100, amount_usd: null, ...over });
const view = (field) => ({ lines: [{ line_id: "L1", description: "CREW", category: "btl_resident_labor", amount_usd: 100000, fields: [field], portions: [] }], persons: [] });

test("a stated share shows its calculated amount; 60% of 100,000 is 60,000 and the line itself is unchanged", () => {
  const line = view(pct()).lines[0];
  assert.equal(percentAmount(line, "60"), 60000);
  assert.equal(percentAmount(line, "0"), 0, "0 is a real, stated zero");
  assert.equal(percentAmount(line, "100.5"), null, "more than 100% has no amount");
  assert.equal(percentAmount(line, ""), null);
  assert.equal(line.amount_usd, 100000);
});

test("a blank share shows the labelled planning assumption, never a stated fact; no assumption shows Unknown", () => {
  const line = view(pct()).lines[0];
  const assumed = percentNote(line, pct(), "");
  assert.equal(assumed.kind, "ASSUMED");
  assert.match(assumed.text, /ASSUMED 100% for planning = 100,000 USD/);
  assert.match(assumed.text, /not verified/);
  const stated = percentNote(line, pct(), "40");
  assert.equal(stated.kind, "STATED");
  assert.equal(stated.amount_usd, 40000);
  const unknown = percentNote(line, pct({ assumed_pct: null, state: "UNKNOWN" }), "");
  assert.equal(unknown.kind, "UNKNOWN");
  assert.equal(unknown.amount_usd, null);
});

test("assumed -> explicit 0% -> partial -> reset only sends what changed, and Reset sends null (back to the default)", () => {
  let v = view(pct());
  let draft = draftFromView(v);
  assert.equal(draft[fieldKey("L1", "canadian_resident_share_pct")], "", "an assumed share is not in the draft as a value");
  assert.deepEqual(changedLineInputs(v, draft).line_facts, [], "nothing is sent for an untouched assumption");
  const key = fieldKey("L1", "canadian_resident_share_pct");
  assert.deepEqual(changedLineInputs(v, { ...draft, [key]: "0" }).line_facts, [{ line_id: "L1", field: "canadian_resident_share_pct", value: 0 }]);
  assert.deepEqual(changedLineInputs(v, { ...draft, [key]: "40" }).line_facts, [{ line_id: "L1", field: "canadian_resident_share_pct", value: 40 }]);
  v = view(pct({ value: 40, state: "STATED", assumed_pct: null, amount_usd: 40000 }));
  draft = draftFromView(v);
  assert.equal(draft[key], "40");
  assert.deepEqual(changedLineInputs(v, { ...draft, [key]: "" }).line_facts, [{ line_id: "L1", field: "canadian_resident_share_pct", value: null }], "Reset clears the stated fact");
  assert.deepEqual(changedLineInputs(v, draft).line_facts, [], "Cancel (restoring the draft) sends nothing");
});

test("invalid shares are caught in the editor before a save: negative, over 100, not a number", () => {
  const v = view(pct());
  const key = fieldKey("L1", "canadian_resident_share_pct");
  assert.match(validateLineDrafts(v, { [key]: "101" })[key], /between 0 and 100%/);
  assert.ok(validateLineDrafts(v, { [key]: "-5" })[key]);
  assert.ok(validateLineDrafts(v, { [key]: "abc" })[key]);
  assert.ok(validateLineDrafts(v, { [key]: "NaN" })[key]);
  assert.deepEqual(validateLineDrafts(v, { [key]: "100" }), {});
  assert.deepEqual(validateLineDrafts(v, { [key]: "0" }), {});
});

test("the editor renders the percent control, calculated amount, assumed label, Reset, and keeps the line's payee_type editable beside people", () => {
  const src = read("components/LineInputsSection.jsx");
  assert.ok(isPercentField(pct()));
  assert.match(src, /data-percent-note=/);
  assert.match(src, /data-percent-state=/);
  assert.match(src, /data-reset-percent=/);
  assert.match(src, /Reset to scenario default/);
  assert.match(src, /data-labour-basis=/);
  assert.match(src, /data-labour-basis-status=/);
  assert.match(src, /ASSUMED FOR PLANNING/);
  assert.match(src, /PRODUCER_STATED/);
  assert.match(src, /EVIDENCED/);
  const superseded = src.match(/const SUPERSEDED = new Set\(\[([^\]]*)\]/)[1];
  assert.ok(!superseded.includes("payee_type"), "payee_type is the line's own classification and stays visible and editable");
});
