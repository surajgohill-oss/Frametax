// Budget-line inputs (NA-RECONCILIATION-24): pure form logic over the served picker `GET /projects/{id}/line-inputs`. Only the lines and fields a rule of the selected programs reads are served.
// Unknown (blank) is never No and never zero: a boolean is Unknown / Yes / No, a number is blank (Unknown) or a real value (0 is a real zero), an enum is Unknown or one of its choices.
// The qualifying portion of a line can never exceed the line amount; a person marked as a line's complete compensation needs an identified person on it. The budget's own classification is shown read-only
// and a stated fact never overwrites it.

const blank = (v) => v === null || v === undefined || String(v).trim() === "";
export const fieldKey = (lineId, name) => `${lineId}:${name}`;
export const portionKey = (lineId, program, uplift) => `${lineId}|${program}|${uplift}`;

const textOf = (f) => (f.value === null || f.value === undefined ? "" : f.kind === "boolean" ? (f.value ? "yes" : "no") : String(f.value));

export function draftFromView(view) {
  const draft = {};
  for (const l of view?.lines ?? []) {
    for (const f of l.fields) draft[fieldKey(l.line_id, f.name)] = textOf(f);
    for (const p of l.portions ?? []) draft[portionKey(l.line_id, p.program, p.uplift)] = p.amount_usd === null || p.amount_usd === undefined ? "" : String(p.amount_usd);
  }
  return draft;
}

function number(text) {
  const t = String(text).trim();
  if (!/^\d+(\.\d*)?$|^\.\d+$/.test(t)) return { error: "Enter a number of at least 0" };
  const n = Number(t);
  return Number.isFinite(n) ? { value: n } : { error: "Enter a finite number" };
}

export function validateLineDrafts(view, draft) {
  const errors = {};
  for (const l of view?.lines ?? []) {
    for (const f of l.fields) {
      const text = draft[fieldKey(l.line_id, f.name)] ?? "";
      if (blank(text) || f.kind !== "number") continue;
      const n = number(text);
      if (n.error) errors[fieldKey(l.line_id, f.name)] = n.error;
      else if (f.max_usd !== null && f.max_usd !== undefined && n.value > f.max_usd + 0.005) errors[fieldKey(l.line_id, f.name)] = `Cannot exceed the line amount ${f.max_usd.toLocaleString()}`;
    }
    for (const p of l.portions ?? []) {
      const k = portionKey(l.line_id, p.program, p.uplift);
      if (blank(draft[k])) continue;
      const n = number(draft[k]);
      if (n.error) errors[k] = n.error;
      else if (n.value > l.amount_usd + 0.005) errors[k] = `The qualifying portion cannot exceed the line amount ${l.amount_usd.toLocaleString()}`;
    }
    const complete = draft[fieldKey(l.line_id, "payee_compensation_complete")];
    if (complete === "yes" && blank(draft[fieldKey(l.line_id, "payee_id")])) errors[fieldKey(l.line_id, "payee_compensation_complete")] = "Identify the person on this line first";
  }
  return errors;
}

function valueOf(f, text) {
  if (blank(text)) return null;
  if (f.kind === "boolean") return text === "yes";
  if (f.kind === "number") return number(text).value;
  return String(text).trim();
}

// only what changed: { line_facts: [{line_id, field, value | null}], uplift_basis: [{program, uplift, line_id, amount_usd | null}] }
export function changedLineInputs(view, draft) {
  const line_facts = [];
  const uplift_basis = [];
  for (const l of view?.lines ?? []) {
    for (const f of l.fields) {
      const now = draft[fieldKey(l.line_id, f.name)] ?? "";
      if (now === textOf(f)) continue;
      line_facts.push({ line_id: l.line_id, field: f.name, value: valueOf(f, now) });
    }
    for (const p of l.portions ?? []) {
      const was = p.amount_usd === null || p.amount_usd === undefined ? "" : String(p.amount_usd);
      const now = draft[portionKey(l.line_id, p.program, p.uplift)] ?? "";
      if (now === was) continue;
      uplift_basis.push({ program: p.program, uplift: p.uplift, line_id: l.line_id, amount_usd: blank(now) ? null : number(now).value });
    }
  }
  return { line_facts, uplift_basis };
}

export const isLineDirty = (view, draft) => {
  const c = changedLineInputs(view, draft);
  return c.line_facts.length + c.uplift_basis.length > 0;
};

// per-person reconciliation shown beside the lines: the person's lines and their total, and whether every line is marked complete
export const personSummary = (view) => (view?.persons ?? []).map((p) => ({ ...p, text: `${p.payee}: ${p.lines.length} line(s), ${p.total_usd.toLocaleString()} USD${p.complete ? "" : " (not every line marked complete)"}` }));
