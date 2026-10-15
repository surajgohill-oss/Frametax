// Several people on ONE budget line (NA-RECONCILIATION-25). Backend path: test_na_line_allocations_controls.py. Pure logic runs the real module; the component contract is a source scan.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { allocationDraftFromView, allocatedTotal, changedAllocations, emptyPerson, isAllocationDirty, unallocated, validateAllocationDrafts } from "../src/lib/lineInputs.js";

const SRC = join(dirname(fileURLToPath(import.meta.url)), "..", "src");
const person_fields = [{ name: "mt_status", label: "Student, veteran or tribal member", kind: "enum", choices: ["none", "student", "veteran_tribal"] }, { name: "mt_tax_withheld", label: "Withheld", kind: "boolean", choices: [] },
  { name: "mt_residency", label: "Residency", kind: "enum", choices: ["resident", "nonresident"] }];
const line = (id, amount, people = [], legacy = false) => ({ line_id: id, amount_usd: amount, category: "btl_crew_labor", fields: [], allocations: { people, person_fields, legacy_single_person: legacy, assigned_usd: 0, unallocated_usd: amount, unallocated_state: "UNKNOWN" } });
const view = (...lines) => ({ lines });

test("an unallocated line is empty, its whole amount is Unknown, and nothing is sent", () => {
  const v = view(line("L1", 1000));
  const ad = allocationDraftFromView(v);
  assert.deepEqual(ad.L1, []);
  assert.equal(unallocated(v.lines[0], ad.L1), 1000);
  assert.deepEqual(changedAllocations(v, ad), []);
});

test("people sum to at most the line, the remainder is Unknown, and exceeding the line is refused", () => {
  const v = view(line("L1", 1000));
  const ok = { L1: [{ ...emptyPerson(), payee_id: "A", amount_usd: "600" }, { ...emptyPerson(), payee_id: "B", amount_usd: "300" }] };
  assert.equal(allocatedTotal(ok.L1), 900);
  assert.equal(unallocated(v.lines[0], ok.L1), 100);
  assert.deepEqual(validateAllocationDrafts(v, ok), {});
  const over = { L1: [{ ...emptyPerson(), payee_id: "A", amount_usd: "700" }, { ...emptyPerson(), payee_id: "B", amount_usd: "400" }] };
  assert.match(validateAllocationDrafts(v, over).L1, /more than the line amount/);
});

test("a person appears once per line, needs a name and an amount, and is in one Montana category across lines", () => {
  const v = view(line("L1", 1000), line("L2", 1000));
  assert.match(validateAllocationDrafts(v, { L1: [{ ...emptyPerson(), payee_id: "A", amount_usd: "1" }, { ...emptyPerson(), payee_id: "a", amount_usd: "1" }] })["L1#1"], /counted once/);
  assert.match(validateAllocationDrafts(v, { L1: [{ ...emptyPerson(), payee_id: "", amount_usd: "1" }] })["L1#0"], /Name or identify/);
  assert.match(validateAllocationDrafts(v, { L1: [{ ...emptyPerson(), payee_id: "A", amount_usd: "" }] })["L1#0"], /Enter this person's compensation/);
  const split = { L1: [{ ...emptyPerson(), payee_id: "A", amount_usd: "1", fields: { mt_status: "student" } }], L2: [{ ...emptyPerson(), payee_id: "A", amount_usd: "1", fields: { mt_status: "veteran_tribal" } }] };
  assert.match(validateAllocationDrafts(v, split)["L2#0"], /exactly one/);
  split.L2[0].fields.mt_status = "student";
  assert.deepEqual(validateAllocationDrafts(v, split), {});
});

test("evidence needs its source, method and confidence together", () => {
  const v = view(line("L1", 1000));
  const bad = { L1: [{ ...emptyPerson(), payee_id: "A", amount_usd: "1", evidence: { source: "payroll", method: "", confidence: "" } }] };
  assert.match(validateAllocationDrafts(v, bad)["L1#0"], /method and confidence/);
});

test("Save sends only changed lines; clearing every person is Reset (null), restoring Unknown", () => {
  const people = [{ payee_id: "A", amount_usd: 400, mt_status: "student" }];
  const v = view(line("L1", 1000, people), line("L2", 500));
  const ad = allocationDraftFromView(v);
  assert.equal(isAllocationDirty(v, ad), false);
  assert.equal(ad.L1[0].fields.mt_status, "student");
  ad.L1[0].amount_usd = "450";
  const sent = changedAllocations(v, ad);
  assert.equal(sent.length, 1);
  assert.deepEqual(sent[0], { line_id: "L1", allocations: [{ payee_id: "A", amount_usd: 450, mt_status: "student" }] });
  ad.L1 = [];
  assert.deepEqual(changedAllocations(v, ad), [{ line_id: "L1", allocations: null }]);
});

test("a legacy single-person line is read as one person and is not re-sent unless edited", () => {
  const v = view(line("L1", 1000, [{ payee_id: "Pat", amount_usd: 1000 }], true));
  const ad = allocationDraftFromView(v);
  assert.equal(ad.L1.length, 1);
  assert.deepEqual(changedAllocations(v, ad), []);
  ad.L1.push({ ...emptyPerson(), payee_id: "Sam", amount_usd: "0" });
  ad.L1[0].amount_usd = "600";
  assert.equal(changedAllocations(v, ad)[0].allocations.length, 2);
});

test("the editor is wired to the one canonical writer, shows the Unknown remainder, and Cancel restores the persisted state", () => {
  const src = readFileSync(join(SRC, "components", "LineInputsSection.jsx"), "utf8");
  assert.match(src, /line_allocations/);
  assert.match(readFileSync(join(SRC, "api.js"), "utf8"), /body: JSON\.stringify\(\{ evidenced, amounts, line_facts, uplift_basis, line_allocations \}\)/, "the client sends allocations to the writer (a browser check caught this being dropped)");
  assert.match(src, /data-line-allocations/);
  assert.match(src, /not assigned to anyone \(Unknown\)/);
  assert.match(src, /data-add-person/);
  assert.match(src, /data-remove-person/);
  assert.match(src, /setAlloc\(allocationDraftFromView\(view\)\)/, "Cancel restores the persisted allocations");
  assert.match(src, /evaluateOnSave/, "Save runs the shared single-flight evaluation (or stays read-only when told not to)");
});
