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
