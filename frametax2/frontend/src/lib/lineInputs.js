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

// ── several people on ONE line (NA-RECONCILIATION-25) ─────────────────────────────────────────────────────────────────────────────────────────────
// The served `line.allocations` = { people: [{payee_id, amount_usd, <person facts>, evidence}], assigned_usd, unallocated_usd, unallocated_state, legacy_single_person, person_fields }. The draft is
// { [lineId]: [{ payee_id, amount_usd (text), fields: {name: text}, evidence: {source, method, confidence} }] }. The people of a line sum to at most the line; the remainder is Unknown (never assigned to anyone);
// one person appears once per line; a person has exactly one Montana category and one residency across the project. A legacy single-person line is shown as one person and sent only if edited.
export const EVIDENCE_METHODS = ["PRODUCER_ASSERTED", "PAYROLL_DOCUMENT", "DEAL_MEMO", "AUTHORITY_DETERMINATION"];
export const EVIDENCE_CONFIDENCES = ["STATED", "DOCUMENTED", "AUTHORITATIVE"];

function personText(spec, v) {
  if (v === null || v === undefined || v === "") return "";
  if (spec.kind === "boolean") return v === true || String(v).toLowerCase() === "true" ? "yes" : "no";
  return String(v);
}

export function allocationDraftFromView(view) {
  const out = {};
  for (const l of view?.lines ?? []) {
    const a = l.allocations;
    if (!a) continue;
    const specs = Object.fromEntries((a.person_fields ?? []).map((s) => [s.name, s]));
    out[l.line_id] = (a.people ?? []).map((p) => ({
      payee_id: p.payee_id,
      amount_usd: p.amount_usd === null || p.amount_usd === undefined ? "" : String(p.amount_usd),
      fields: Object.fromEntries(Object.entries(specs).map(([n, s]) => [n, personText(s, p[n])])),
      evidence: { source: p.evidence?.source ?? "", method: p.evidence?.method ?? "", confidence: p.evidence?.confidence ?? "" },
    }));
  }
  return out;
}

export const emptyPerson = () => ({ payee_id: "", amount_usd: "", fields: {}, evidence: { source: "", method: "", confidence: "" } });

const norm = (rows) => JSON.stringify((rows ?? []).map((r) => ({ n: String(r.payee_id).trim(), a: String(r.amount_usd).trim(), f: Object.entries(r.fields ?? {}).filter(([, v]) => v !== "").sort(), e: r.evidence?.source ? r.evidence : null })));

export const allocatedTotal = (rows) => (rows ?? []).reduce((s, r) => s + (blank(r.amount_usd) || number(r.amount_usd).error ? 0 : number(r.amount_usd).value), 0);
export const unallocated = (line, rows) => Math.max(0, Math.round((line.amount_usd - allocatedTotal(rows)) * 100) / 100);

export function validateAllocationDrafts(view, ad) {
  const errors = {};
  const seen = {};
  for (const l of view?.lines ?? []) {
    const rows = ad[l.line_id] ?? [];
    const names = new Set();
    rows.forEach((r, i) => {
      const k = `${l.line_id}#${i}`;
      const name = String(r.payee_id).trim();
      if (!name) { errors[k] = "Name or identify the person"; return; }
      if (names.has(name.toLowerCase())) errors[k] = `${name} appears twice on this line; a person is counted once`;
      names.add(name.toLowerCase());
      const n = blank(r.amount_usd) ? { error: "Enter this person's compensation on the line" } : number(r.amount_usd);
      if (n.error) errors[k] = errors[k] ?? n.error;
      for (const [fname, label] of [["mt_status", "student / veteran-tribal / neither"], ["mt_residency", "residency"]]) {
        const v = r.fields?.[fname];
        if (!v) continue;
        const prior = (seen[name.toLowerCase()] ??= {})[fname];
        if (prior && prior.value !== v) errors[k] = errors[k] ?? `${name} is '${prior.value}' on another line and '${v}' here: a person is in exactly one ${label} category`;
        else seen[name.toLowerCase()][fname] = { value: v };
      }
      if (r.evidence?.source && (!r.evidence.method || !r.evidence.confidence)) errors[k] = errors[k] ?? "Evidence needs its method and confidence";
    });
    if (allocatedTotal(rows) > l.amount_usd + 0.005) errors[l.line_id] = `The people carry ${allocatedTotal(rows).toLocaleString()}, more than the line amount ${l.amount_usd.toLocaleString()}`;
  }
  return errors;
}

export function changedAllocations(view, ad) {
  const was = allocationDraftFromView(view);
  const out = [];
  for (const l of view?.lines ?? []) {
    if (norm(ad[l.line_id]) === norm(was[l.line_id])) continue;
    const rows = ad[l.line_id] ?? [];
    if (!rows.length) { out.push({ line_id: l.line_id, allocations: null }); continue; }
    const specs = Object.fromEntries((l.allocations?.person_fields ?? []).map((s) => [s.name, s]));
    out.push({
      line_id: l.line_id,
      allocations: rows.map((r) => {
        const person = { payee_id: String(r.payee_id).trim(), amount_usd: number(r.amount_usd).value };
        for (const [n, text] of Object.entries(r.fields ?? {})) if (specs[n] && !blank(text)) person[n] = valueOf(specs[n], text);
        if (r.evidence?.source) person.evidence = { source: r.evidence.source.trim(), method: r.evidence.method, confidence: r.evidence.confidence };
        return person;
      }),
    });
  }
  return out;
}

export const isAllocationDirty = (view, ad) => changedAllocations(view, ad).length > 0;
