// Resolved requirements (NA-RECONCILIATION-22): pure logic over the served view `production.program_facts`.
// Every fact arrives with a value AND a provenance (VERIFIED, PRODUCER_STATED, SCENARIO_ASSUMED, SCHEDULE_DERIVED, UNKNOWN). Derived and scenario-assumed facts are read-only; a control exists only for a genuine
// producer decision or for evidence the system cannot hold. A yes/no predicate is tri-state (Yes / No / Unknown); an election between alternatives offers Yes (the chosen alternative) or Unknown, never No.
// The payload carries ONLY what the producer changed: `evidenced: { key: true | false | null }`, `amounts: { key: number | null }`; null clears to Unknown.

export const PROVENANCE_LABEL = {
  VERIFIED: "Verified evidence",
  PRODUCER_STATED: "Producer-stated",
  SCENARIO_ASSUMED: "Scenario assumption",
  SCHEDULE_DERIVED: "From the schedule",
  BUDGET_DERIVED: "From the budget",
  UNKNOWN: "Unknown",
};

export const provenanceLabel = (p) => PROVENANCE_LABEL[p] ?? PROVENANCE_LABEL.UNKNOWN;
export const isReadOnly = (fact) => fact.editable === false;
export const isElection = (fact) => fact.kind === "election";
export const booleanOptions = (fact) => (isElection(fact) ? ["", "yes"] : ["", "yes", "no"]);

const textOf = (f) => {
  if (f.kind === "number") return f.state === "VALUE" && f.provenance === "PRODUCER_STATED" ? String(f.value) : "";
  return f.state === "TRUE" ? "yes" : f.state === "FALSE" ? "no" : "";
};

export function draftFrom(group) {
  const draft = {};
  for (const f of group.facts) if (!isReadOnly(f)) draft[f.key] = textOf(f);
  return draft;
}

function parseNumber(text) {
  const t = String(text ?? "").trim();
  if (t === "") return { unknown: true };
  if (!/^[+-]?(\d+(\.\d*)?|\.\d+)$/.test(t)) return { error: "Enter a number" };
  const n = Number(t);
  return Number.isFinite(n) ? { value: n } : { error: "Enter a finite number" };
}

export function validateFact(fact, text) {
  if (fact.kind !== "number") return null;
  const parsed = parseNumber(text);
  if (parsed.unknown) return null;
  if (parsed.error) return parsed.error;
  if (fact.whole && !Number.isInteger(parsed.value)) return "Whole numbers only";
  if (parsed.value < fact.min || parsed.value > fact.max) return `Between ${fact.min} and ${fact.max}`;
  return null;
}

export function validateDraft(group, draft) {
  const errors = {};
  for (const f of group.facts) {
    if (isReadOnly(f)) continue;
    const message = validateFact(f, draft[f.key]);
    if (message) errors[f.key] = message;
  }
  return errors;
}

export function changedFacts(group, draft) {
  const evidenced = {};
  const amounts = {};
  for (const f of group.facts) {
    if (isReadOnly(f)) continue;                                         // a derived or assumed fact is never written back
    const was = textOf(f);
    const now = draft[f.key] ?? "";
    if (f.kind === "number") {
      const a = parseNumber(now);
      const b = parseNumber(was);
      if ((a.unknown && b.unknown) || (!a.unknown && !b.unknown && a.value === b.value)) continue;
      amounts[f.key] = a.unknown ? null : a.value;
    } else {
      if (now === was) continue;
      if (now === "no" && isElection(f)) continue;                        // an election is never answered No: the chosen alternative is stated instead
      evidenced[f.key] = now === "yes" ? true : now === "no" ? false : null;
    }
  }
  return { evidenced, amounts };
}

export const isDirty = (group, draft) => {
  const { evidenced, amounts } = changedFacts(group, draft);
  return Object.keys(evidenced).length + Object.keys(amounts).length > 0;
};

// Choosing Yes on one side of an exclusive pair leaves the partner Unknown in the draft (the server replaces the stored partner the same way).
export function chooseBoolean(group, draft, key, choice) {
  const next = { ...draft, [key]: choice };
  const fact = group.facts.find((f) => f.key === key);
  if (choice === "yes" && fact?.exclusive_with && !isReadOnly(group.facts.find((f) => f.key === fact.exclusive_with) ?? {})) next[fact.exclusive_with] = "";
  return next;
}

// What is still needed: facts that are Unknown AND that the producer can state. Unknown is a different list from No.
export function stillNeeded(view) {
  const needed = [];
  for (const g of view?.groups ?? []) for (const f of g.facts) if (f.state === "UNKNOWN" && !isReadOnly(f)) needed.push({ group: g.title, key: f.key, requirement: f.requirement ?? f.label });
  return needed;
}

export const factStatusText = (f) => {
  if (f.kind === "number") return f.state === "VALUE" ? `${f.value}${f.unit === "USD" ? " USD" : ""}` : "Unknown";
  return f.state === "TRUE" ? "Yes" : f.state === "FALSE" ? "No" : "Unknown";
};

// The Missouri rate display from the served ladder: 20% base, then each statutory increase with its state. 15% is a share threshold of the Missouri filming, never 15 points.
export function ladderLines(ladder) {
  if (!ladder) return [];
  const lines = [{ id: "base", text: `Base ${ladder.base_pct}%`, state: "TRUE" }];
  for (const s of ladder.steps) lines.push({ id: s.id, text: `+${s.points} points`, state: s.state, key: s.fact_key });
  lines.push({ id: "total", text: `Confirmed ${ladder.confirmed_pct}% · up to ${ladder.potential_pct}% · maximum ${ladder.max_pct}%`, state: "TOTAL" });
  return lines;
}

// ── relevance (NA-RECONCILIATION-23): only what could change the selected structure's eligibility or value ─────────────────────────────────────────

export function structurePrograms(structure) {
  if (!structure) return [];
  const slugs = new Set([...(structure.program_slugs ?? []), ...(structure.claimed_program_ids ?? [])]);
  for (const c of structure.component_allocations ?? []) if (c.program_slug) slugs.add(c.program_slug);
  for (const s of structure.segments ?? []) if (s.program_slug) slugs.add(s.program_slug);
  return [...slugs];
}

const SECTION_OF = { SATISFIED: "satisfied", FAILED: "failed", EXTERNAL_APPROVAL: "approval", CONDITIONAL_UPSIDE: "upside", PRODUCER_INPUT: "input" };
export const SECTION_ORDER = ["input", "approval", "upside", "failed", "satisfied"];
export const SECTION_TITLE = {
  input: "Producer input needed",
  approval: "External approval required",
  upside: "Conditional upside",
  failed: "Failed requirements",
  satisfied: "Already satisfied",
};

export function relevantFacts(view, structure) {
  const programs = new Set(structurePrograms(structure));
  const out = [];
  if (!programs.size) return out;
  for (const g of view?.groups ?? []) for (const f of g.facts) {
    const fp = f.programs?.length ? f.programs : g.programs ?? [];
    if (fp.some((p) => programs.has(p))) out.push({ ...f, group: g.title, groupId: g.id });
  }
  return out;
}

// Five sections; a fact appears in exactly one. Derived / verified / assumed facts are "satisfied" (collapsed); a stated No is "failed" with its pricing effect.
export function sectionsFor(view, structure) {
  const sections = { input: [], approval: [], upside: [], failed: [], satisfied: [] };
  for (const f of relevantFacts(view, structure)) sections[SECTION_OF[f.category] ?? "input"].push(f);
  return sections;
}

export function structureUpside(structure) {
  return (structure?.ceiling_missing_facts ?? []).filter((m) => Number(m.unlocks_incentive_usd) > 0).map((m) => ({
    id: m.fact_id, description: m.description, usd: Number(m.unlocks_incentive_usd), program: m.program_slug, note: m.note ?? null,
  }));
}

export const hasMissouri = (structure) => structurePrograms(structure).includes("us_mo_motion_media_production_tax_credit");

export function relevantScenarioRules(view, structure) {
  const programs = new Set(structurePrograms(structure));
  return (view?.scenario_rules ?? []).filter((r) => programs.has(r.program));
}

export function relevantLocationNeeds(view, structure) {
  const programs = new Set(structurePrograms(structure));
  const needs = [];
  for (const f of relevantFacts(view, structure)) {
    if (f.state === "UNKNOWN" && ["LOCALITY", "SCENARIO_PLACEMENT"].includes(f.derivation_class) && f.requirement && /location/i.test(f.requirement)) needs.push({ key: f.key, requirement: f.requirement });
  }
  return programs.size ? needs : [];
}
