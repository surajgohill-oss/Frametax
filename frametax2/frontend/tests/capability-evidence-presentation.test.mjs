import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { structureStatusDetail, fitSummaryText, capabilityEvidenceText, fitText } from "../src/lib/alternativeLabels.js";
import { structureStory } from "../src/lib/globeStructure.js";
import { buildCandidateDetail } from "../src/lib/globeData.js";

const read = (p) => readFileSync(new URL(p, import.meta.url), "utf8");
const EVIDENCE = [
  { jurisdiction: "QA", category: "desert_arid", token: "desert_environments", status: "SUPPORTED", terminal_status: "AUTHORITY_VERIFIED_SUPPORTED",
    hard_requirement: true, source_title: "Global Land Cover-SHARE", evidence_tier: "INTERGOVERNMENTAL_DATASET" },
];

test("the segment Inspector and the candidate Inspector carry the SAME served capability evidence", () => {
  const structure = {
    structure_id: "s1", label: "Qatar", primary_jurisdiction: "QA", participants: ["QA"], segments: [], component_allocations: [],
    production_fit_status: "WORKABLE", production_fit_legs: ["QA"], production_fit_reasons: [],
    production_fit_soft_signals: { matched: ["QA:urban_environments"], mismatched: [], unassessed: [] }, production_fit_capability_evidence: EVIDENCE,
  };
  assert.deepEqual(structureStatusDetail(structure).production_fit_capability_evidence, EVIDENCE);
  assert.deepEqual(buildCandidateDetail(structure).production_fit_capability_evidence, EVIDENCE);
});

test("hover, Inspector and every fit surface read only the served evidence (no capability truth in the frontend)", () => {
  const files = ["../src/shell/Inspector.jsx", "../src/lib/globeData.js", "../src/components/GlobeHoverCard.jsx", "../src/lib/alternativeLabels.js"];
  for (const f of files) {
    const src = read(f);
    assert.ok(/production_fit_capability_evidence|capabilityEvidenceText|fitSummaryText|fitSummary/.test(src), f);
    assert.ok(!/desert_environments\s*[:=]|LOCATION_CENSUS|location_capability_cells|jurisdiction_capability_profile/.test(src.replace(/\/\/.*$/gm, "")), f);
  }
  assert.ok((read("../src/shell/Inspector.jsx").match(/<CapabilityEvidence evidence=\{data\.production_fit_capability_evidence\} \/>/g) || []).length === 3);
  assert.match(read("../src/components/GlobeHoverCard.jsx"), /hover\.productionFitSummary/);
  assert.match(read("../src/components/GlobeHoverCard.jsx"), /story\.fitSummary/);
});

test("hover story, hover record and Inspector share one served text for fit + soft signals + capability evidence", () => {
  const structure = {
    structure_id: "s1", label: "Qatar", primary_jurisdiction: "QA", participants: ["QA"], segments: [], component_allocations: [],
    production_fit_status: "WORKABLE", production_fit_legs: ["QA"], production_fit_reasons: [],
    production_fit_soft_signals: { matched: ["QA:urban_environments"], mismatched: [], unassessed: ["QA:tropical_environments"] },
    production_fit_capability_evidence: EVIDENCE,
  };
  const summary = fitSummaryText(structure);
  assert.match(summary, /^Workable fit · physical production: QA/);
  assert.match(summary, /Soft signals — supported: Urban; not assessed/);
  assert.match(summary, /Capability evidence — .*supported in QA \(hard requirement\) \[Global Land Cover-SHARE, intergovernmental dataset\]/);
  assert.equal(structureStory(structure).fitSummary, summary);
  assert.ok(summary.startsWith(fitText(structure)));
  assert.equal(capabilityEvidenceText([]), null);
  assert.equal(fitSummaryText({}), null);
});
