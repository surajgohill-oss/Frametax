import { useCallback, useEffect, useState } from "react";
import { getLineInputs, postProgramFacts } from "../api";
import { runEvaluation, useEvaluationRun } from "../lib/evaluationRun";
import { EVIDENCE_CONFIDENCES, EVIDENCE_METHODS, allocatedTotal, allocationDraftFromView, changedAllocations, changedLineInputs, draftFromView, emptyPerson, fieldKey, isAllocationDirty, isLineDirty, isPercentField, percentNote, personSummary, portionKey, unallocated, validateAllocationDrafts, validateLineDrafts } from "../lib/lineInputs";
import { structurePrograms } from "../lib/resolvedRequirements";
import { RetainedSaveNote } from "./EvaluationStatus";

// Budget-line inputs (NA-RECONCILIATION-24), a section of the Resolved Requirements panel. A picker over the project's budget lines that offers, for the selected structure's programs, only the lines and fields a
// rule actually reads: the person paid, whether the line is their whole compensation, role, status, residency, service location, payee type, payment status, look-through wages, assistance, composer portion,
// producer position, Montana status / withholding, and the qualifying portion of a line. The budget's own classification is shown read-only and never overwritten. Unknown is not No; a portion cannot exceed its
// line; a person's total is the sum of the lines assigned to them. Save stores only what changed through the ONE canonical writer (ProjectFact line facts / uplift basis) and runs the shared single-flight
// evaluation once; Cancel restores the persisted state; clearing a field resets it to Unknown.
// once a line has people, its per-line single-person identity fields are replaced by the people editor below them (a line-level classification with no person stays editable) (one canonical owner: `line_fact:<line>:allocations`)
// `payee_type` is the line's own classification (the Canadian labour basis reads it per line); only the person identity and Montana person facts are replaced by the people editor.
const SUPERSEDED = new Set(["payee_id", "payee_compensation_complete", "mt_status", "mt_tax_withheld", "mt_residency"]);
export default function LineInputsSection({ projectId, structure, refreshKey, onSaved, evaluateOnSave = true }) {
  const programs = structurePrograms(structure);
  const programKey = programs.slice().sort().join(",");
  const [view, setView] = useState(null);
  const [draft, setDraft] = useState({});
  const [alloc, setAlloc] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedNotEvaluated, setSavedNotEvaluated] = useState(false);
  const run = useEvaluationRun(projectId);
  const load = useCallback(async () => {
    if (!projectId || !programKey) { setView(null); return; }
    try {
      const res = await getLineInputs(projectId, programKey.split(","));
      setView(res.line_inputs);
      setDraft(draftFromView(res.line_inputs));
      setAlloc(allocationDraftFromView(res.line_inputs));
    } catch (err) {
      setError((err && err.message) || "The budget lines could not be read.");
    }
  }, [projectId, programKey]);
  useEffect(() => { load(); }, [load, refreshKey]);
  if (!projectId || !view || !view.lines.length) return null;

  const allocErrors = validateAllocationDrafts(view, alloc);
  const errors = { ...validateLineDrafts(view, draft), ...allocErrors };
  const dirty = isLineDirty(view, draft) || isAllocationDirty(view, alloc);
  const locked = saving || run.running;

  async function save() {
    if (saving || run.running) return;
    if (Object.keys(errors).length) { setError("Fix the highlighted fields first."); return; }
    const { line_facts, uplift_basis } = changedLineInputs(view, draft);
    const line_allocations = changedAllocations(view, alloc);
    setSaving(true);
    setError(null);
    setSavedNotEvaluated(false);
    try {
      await postProgramFacts(projectId, { line_facts, uplift_basis, line_allocations });
      await load();
      if (evaluateOnSave) await runEvaluation(projectId);
      else setSavedNotEvaluated(true);
      onSaved?.();
    } catch (err) {
      setError((err && err.message) || "The line inputs could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  const control = (l, f) => {
    const k = fieldKey(l.line_id, f.name);
    const value = draft[k] ?? "";
    const set = (v) => setDraft((d) => ({ ...d, [k]: v }));
    if (f.kind === "enum") return <select className="pd-select" aria-label={f.label} value={value} disabled={locked} onChange={(e) => set(e.target.value)}><option value="">Unknown</option>{f.choices.map((c) => <option key={c} value={c}>{c.replace(/_/g, " ")}</option>)}</select>;
    if (f.kind === "boolean") return <select className="pd-select" aria-label={f.label} value={value} disabled={locked} onChange={(e) => set(e.target.value)}><option value="">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select>;
    if (isPercentField(f)) return <input className={`pd-select ${value ? "" : "pd-missing"}`} aria-label={f.label} placeholder={f.assumed_pct != null ? `Assumed ${f.assumed_pct}%` : "Unknown"} inputMode="decimal" value={value} disabled={locked} onChange={(e) => set(e.target.value)} />;
    return <input className={`pd-select ${value ? "" : "pd-missing"}`} aria-label={f.label} placeholder="Unknown" inputMode={f.kind === "number" ? "decimal" : "text"} value={value} disabled={locked} onChange={(e) => set(e.target.value)} />;
  };

  const setRows = (l, fn) => setAlloc((a) => ({ ...a, [l.line_id]: fn(a[l.line_id] ?? []) }));
  const patchRow = (l, i, patch) => setRows(l, (rows) => rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const allocationEditor = (l) => {
    const rows = alloc[l.line_id] ?? [];
    const remainder = unallocated(l, rows);
    return (
      <div className="pd-name rr-fact" data-line-allocations={l.line_id} data-unallocated={remainder}>
        <span className="text-tertiary">People paid from this line · each person is counted once; the part not assigned to anyone stays Unknown</span>
        {rows.map((r, i) => (
          <div key={i} className="rr-fact" data-allocation-row={`${l.line_id}#${i}`}>
            <input className="pd-select" aria-label="Person" placeholder="Person name or id" value={r.payee_id} disabled={locked} onChange={(e) => patchRow(l, i, { payee_id: e.target.value })} />
            <input className={`pd-select ${r.amount_usd ? "" : "pd-missing"}`} aria-label="Compensation on this line (USD)" placeholder="Compensation on this line" inputMode="decimal" value={r.amount_usd} disabled={locked} onChange={(e) => patchRow(l, i, { amount_usd: e.target.value })} />
            {(l.allocations.person_fields ?? []).map((f) => (
              f.kind === "number"
                ? <input key={f.name} className="pd-select" aria-label={f.label} placeholder={`${f.label} (Unknown)`} inputMode="decimal" value={r.fields?.[f.name] ?? ""} disabled={locked} onChange={(e) => patchRow(l, i, { fields: { ...r.fields, [f.name]: e.target.value } })} />
                : <select key={f.name} className="pd-select" aria-label={f.label} value={r.fields?.[f.name] ?? ""} disabled={locked} onChange={(e) => patchRow(l, i, { fields: { ...r.fields, [f.name]: e.target.value } })}>
                    <option value="">{f.label}: Unknown</option>
                    {(f.kind === "boolean" ? ["yes", "no"] : f.choices).map((c) => <option key={c} value={c}>{`${f.label}: ${String(c).replace(/_/g, " ")}`}</option>)}
                  </select>
            ))}
            <input className="pd-select" aria-label="Evidence source" placeholder="Evidence source (payroll document, deal memo…)" value={r.evidence?.source ?? ""} disabled={locked} onChange={(e) => patchRow(l, i, { evidence: { ...r.evidence, source: e.target.value } })} />
            <select className="pd-select" aria-label="Evidence method" value={r.evidence?.method ?? ""} disabled={locked} onChange={(e) => patchRow(l, i, { evidence: { ...r.evidence, method: e.target.value } })}><option value="">Method</option>{EVIDENCE_METHODS.map((m) => <option key={m} value={m}>{m.replace(/_/g, " ").toLowerCase()}</option>)}</select>
            <select className="pd-select" aria-label="Evidence confidence" value={r.evidence?.confidence ?? ""} disabled={locked} onChange={(e) => patchRow(l, i, { evidence: { ...r.evidence, confidence: e.target.value } })}><option value="">Confidence</option>{EVIDENCE_CONFIDENCES.map((m) => <option key={m} value={m}>{m.toLowerCase()}</option>)}</select>
            <button type="button" className="ghost-action" disabled={locked} onClick={() => setRows(l, (rs) => rs.filter((_, j) => j !== i))} data-remove-person={`${l.line_id}#${i}`}>Remove person</button>
            {allocErrors[`${l.line_id}#${i}`] && <span className="eval-status eval-status-error eval-status-compact" role="alert" data-line-error={`${l.line_id}#${i}`}>{allocErrors[`${l.line_id}#${i}`]}</span>}
          </div>
        ))}
        <div className="text-tertiary" data-allocation-summary={l.line_id}>
          Assigned {allocatedTotal(rows).toLocaleString()} of {l.amount_usd.toLocaleString()} USD · {remainder > 0.005 ? `${remainder.toLocaleString()} USD not assigned to anyone (Unknown)` : allocatedTotal(rows) > l.amount_usd + 0.005 ? "more than the line amount" : "fully assigned"}
          {l.allocations.legacy_single_person && rows.length === 1 && " · read from the earlier single-person entry"}
        </div>
        <button type="button" className="ghost-action" disabled={locked} onClick={() => setRows(l, (rs) => [...rs, emptyPerson()])} data-add-person={l.line_id}>Add person</button>
        {allocErrors[l.line_id] && <span className="eval-status eval-status-error eval-status-compact" role="alert" data-line-error={l.line_id}>{allocErrors[l.line_id]}</span>}
      </div>
    );
  };

  return (
    <details className="pd-person" open data-testid="line-inputs" data-requirements-section="line-inputs">
      <summary className="pd-row">
        <span className="pd-ident"><span className="pd-role">Budget lines</span><span className="pd-name text-tertiary">Only the lines and facts a rule of the selected programs reads</span></span>
        <span className="pd-col-label">{view.lines.length} line(s)</span>
      </summary>
      {personSummary(view).map((p) => <div key={p.payee} className="pd-row" data-person={p.payee}><div className="pd-ident"><span className="pd-name text-tertiary">{p.text}</span></div></div>)}
      {view.lines.map((l) => (
        <div key={l.line_id} className="pd-row rr-line" data-line={l.line_id} data-line-category={l.category}>
          <div className="pd-ident">
            <span className="pd-role">{l.description}</span>
            <span className="pd-name text-tertiary" data-line-derived={l.line_id}>Budget classification: {String(l.category).replace(/_/g, " ")} (derived, read-only) · {l.amount_usd.toLocaleString()} USD</span>
            {l.fields.filter((f) => !((alloc[l.line_id]?.length ?? 0) > 0 && SUPERSEDED.has(f.name))).map((f) => (
              <label key={f.name} className={`pd-name rr-fact rr-prov-${f.state === "STATED" ? "producer_stated" : "unknown"}`} data-line-field={fieldKey(l.line_id, f.name)} data-field-state={f.state}>
                <span className="text-tertiary">{f.label} · {f.consumer}</span>
                {control(l, f)}
                {isPercentField(f) && (() => {
                  const note = percentNote(l, f, draft[fieldKey(l.line_id, f.name)] ?? "");
                  return (
                    <span className="text-tertiary" data-percent-note={fieldKey(l.line_id, f.name)} data-percent-state={note.kind} data-percent-amount={note.amount_usd ?? ""}>
                      {note.text}
                      {!(draft[fieldKey(l.line_id, f.name)] ?? "").trim() ? null : <button type="button" className="ghost-action" disabled={locked} data-reset-percent={fieldKey(l.line_id, f.name)}
                        onClick={(e) => { e.preventDefault(); setDraft((d) => ({ ...d, [fieldKey(l.line_id, f.name)]: "" })); }}>Reset to scenario default</button>}
                    </span>
                  );
                })()}
                {errors[fieldKey(l.line_id, f.name)] && <span className="eval-status eval-status-error eval-status-compact" role="alert" data-line-error={fieldKey(l.line_id, f.name)}>{errors[fieldKey(l.line_id, f.name)]}</span>}
              </label>
            ))}
            {view.canadian_labour?.lines?.[l.line_id] && (() => {
              const d = view.canadian_labour.lines[l.line_id];
              return <span className="pd-name text-tertiary" data-labour-basis={l.line_id}>Federal PSTC labour basis: {d.stated_eligible_usd.toLocaleString()} USD from stated facts{d.planning_eligible_usd != null && d.planning_eligible_usd !== d.stated_eligible_usd ? ` · ${d.planning_eligible_usd.toLocaleString()} USD planning estimate with the ASSUMED default (not priced, not verified)` : ""}{d.share_basis === "STATED" && d.eligible_share_pct != null ? ` · ${d.eligible_share_pct}% of the line` : ""}</span>;
            })()}
            {l.allocations && allocationEditor(l)}
            {(l.portions ?? []).map((p) => {
              const k = portionKey(l.line_id, p.program, p.uplift);
              return (
                <label key={k} className="pd-name rr-fact" data-line-portion={k}>
                  <span className="text-tertiary">Qualifying portion for {p.uplift.replace(/_/g, " ")} (USD, at most {l.amount_usd.toLocaleString()}) · {p.text}</span>
                  <input className={`pd-select ${draft[k] ? "" : "pd-missing"}`} aria-label={`Qualifying portion ${p.uplift}`} placeholder="Unknown" inputMode="decimal" value={draft[k] ?? ""} disabled={locked}
                    onChange={(e) => setDraft((d) => ({ ...d, [k]: e.target.value }))} />
                  {errors[k] && <span className="eval-status eval-status-error eval-status-compact" role="alert" data-line-error={k}>{errors[k]}</span>}
                </label>
              );
            })}
          </div>
        </div>
      ))}
      <div className="pd-row">
        <button type="button" className="ghost-action" disabled={!dirty || Object.keys(errors).length > 0 || locked} onClick={save} data-save-lines="true">{saving ? "Saving…" : "Save line inputs"}</button>
        <button type="button" className="ghost-action" disabled={!dirty || locked} onClick={() => { setDraft(draftFromView(view)); setAlloc(allocationDraftFromView(view)); }} data-cancel-lines="true">Cancel</button>
      </div>
      {error && <div className="eval-status eval-status-error eval-status-compact" role="alert" data-lines-error="true">{error}</div>}
      {savedNotEvaluated && <RetainedSaveNote />}
    </details>
  );
}
