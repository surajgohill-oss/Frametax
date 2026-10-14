// Producer-stated program facts (NA-RECONCILIATION-21): pure form logic over the served view `production.program_facts`.
// Unknown is a blank / "Unknown" choice, never zero and never No. A yes/no fact can only be Stated or Unknown; a number is a finite value inside the served bounds (whole when the view says so).
// The payload carries ONLY what the producer changed: `evidenced: { key: true | null }`, `amounts: { key: number | null }`; null clears to Unknown.

export function draftFrom(group) {
  const draft = {};
  for (const f of group.facts) draft[f.key] = f.kind === "boolean" ? (f.state === "STATED" ? "yes" : "") : (f.state === "STATED" ? String(f.value) : "");
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
  if (fact.kind === "boolean") return null;
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
    const message = validateFact(f, draft[f.key]);
    if (message) errors[f.key] = message;
  }
  return errors;
}

export function changedFacts(group, draft) {
  const evidenced = {};
  const amounts = {};
  for (const f of group.facts) {
    const was = f.kind === "boolean" ? (f.state === "STATED" ? "yes" : "") : (f.state === "STATED" ? String(f.value) : "");
    const now = draft[f.key] ?? "";
    if (f.kind === "boolean") {
      if (now === was) continue;
      evidenced[f.key] = now === "yes" ? true : null;                    // never false: leaving a statement clears it to Unknown
    } else {
      const a = parseNumber(now);
      const b = parseNumber(was);
      if ((a.unknown && b.unknown) || (!a.unknown && !b.unknown && a.value === b.value)) continue;
      amounts[f.key] = a.unknown ? null : a.value;
    }
  }
  return { evidenced, amounts };
}

export const isDirty = (group, draft) => {
  const { evidenced, amounts } = changedFacts(group, draft);
  return Object.keys(evidenced).length + Object.keys(amounts).length > 0;
};

// Choosing one side of an exclusive pair leaves the partner Unknown in the draft (the server replaces the stored partner the same way).
export function chooseBoolean(group, draft, key, checked) {
  const next = { ...draft, [key]: checked ? "yes" : "" };
  const fact = group.facts.find((f) => f.key === key);
  if (checked && fact?.exclusive_with) next[fact.exclusive_with] = "";
  return next;
}
