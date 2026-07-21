// Regression guard for the frozen ui-baseline-v1 scenario-card title
// contract (lib/format.jsx scenarioDisplay). The frozen prototype titles a
// single-jurisdiction card — baseline OR full relocation — with the plain
// jurisdiction name ("Mauritius" / "Malta" / "Greece"); the structure type
// is conveyed by badge + subtitle, never by prepended wording. A post-freeze
// commit (b73b432) introduced "Relocate to X"; this test keeps it removed.
//
// format.jsx is JSX and cannot be imported by plain Node, so this is a
// source-level guard (same lightweight style as test_today_compute.mjs).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import assert from "node:assert";

const __dirname = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(__dirname, "../src/lib/format.jsx"), "utf8");
// Strip line comments so the rationale comment mentioning the removed
// wording never trips the guard.
const code = src.replace(/\/\/.*$/gm, "");

let passed = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); console.log(`ok   - ${msg}`); passed++; };

ok(!/Relocate to/.test(code),
  "no 'Relocate to' wording remains in scenarioDisplay (frozen: plain jurisdiction name)");
ok(/structure_type === "single_country" \|\| structure\.structure_type === "full_relocation"/.test(code),
  "single_country and full_relocation share the plain-jurisdiction-name title branch");
ok(/title = jurName\(primary\);/.test(code),
  "the shared branch titles the card with jurName(primary) — canonical primary_jurisdiction");
ok(/scenarioDisplay\(structure\)/.test(src) || /export function scenarioDisplay/.test(src),
  "scenarioDisplay remains the single canonical title formatter");

console.log(`\nAll ${passed} tests passed.`);
