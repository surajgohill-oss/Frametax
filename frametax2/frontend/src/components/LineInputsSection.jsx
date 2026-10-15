import { useCallback, useEffect, useState } from "react";
import { getLineInputs, postProgramFacts } from "../api";
import { runEvaluation, useEvaluationRun } from "../lib/evaluationRun";
import { changedLineInputs, draftFromView, fieldKey, isLineDirty, personSummary, portionKey, validateLineDrafts } from "../lib/lineInputs";
import { structurePrograms } from "../lib/resolvedRequirements";
import { RetainedSaveNote } from "./EvaluationStatus";

// Budget-line inputs (NA-RECONCILIATION-24), a section of the Resolved Requirements panel. A picker over the project's budget lines that offers, for the selected structure's programs, only the lines and fields a
// rule actually reads: the person paid, whether the line is their whole compensation, role, status, residency, service location, payee type, payment status, look-through wages, assistance, composer portion,
// producer position, Montana status / withholding, and the qualifying portion of a line. The budget's own classification is shown read-only and never overwritten. Unknown is not No; a portion cannot exceed its
// line; a person's total is the sum of the lines assigned to them. Save stores only what changed through the ONE canonical writer (ProjectFact line facts / uplift basis) and runs the shared single-flight
// evaluation once; Cancel restores the persisted state; clearing a field resets it to Unknown.
export default function LineInputsSection({ projectId, structure, refreshKey, onSaved, evaluateOnSave = true }) {
  const programs = structurePrograms(structure);
  const programKey = programs.slice().sort().join(",");
  const [view, setView] = useState(null);
  const [draft, setDraft] = useState({});
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
    } catch (err) {
      setError((err && err.message) || "The budget lines could not be read.");
    }
  }, [projectId, programKey]);
  useEffect(() => { load(); }, [load, refreshKey]);
  if (!projectId || !view || !view.lines.length) return null;

  const errors = validateLineDrafts(view, draft);
  const dirty = isLineDirty(view, draft);
  const locked = saving || run.running;

  async function save() {
    if (saving || run.running) return;
    if (Object.keys(errors).length) { setError("Fix the highlighted fields first."); return; }
    const { line_facts, uplift_basis } = changedLineInputs(view, draft);
    setSaving(true);
    setError(null);
    setSavedNotEvaluated(false);
    try {
      await postProgramFacts(projectId, { line_facts, uplift_basis });
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
    return <input className={`pd-select ${value ? "" : "pd-missing"}`} aria-label={f.label} placeholder="Unknown" inputMode={f.kind === "number" ? "decimal" : "text"} value={value} disabled={locked} onChange={(e) => set(e.target.value)} />;
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
            {l.fields.map((f) => (
              <label key={f.name} className={`pd-name rr-fact rr-prov-${f.state === "STATED" ? "producer_stated" : "unknown"}`} data-line-field={fieldKey(l.line_id, f.name)} data-field-state={f.state}>
                <span className="text-tertiary">{f.label} · {f.consumer}</span>
                {control(l, f)}
                {errors[fieldKey(l.line_id, f.name)] && <span className="eval-status eval-status-error eval-status-compact" role="alert" data-line-error={fieldKey(l.line_id, f.name)}>{errors[fieldKey(l.line_id, f.name)]}</span>}
              </label>
            ))}
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
        <button type="button" className="ghost-action" disabled={!dirty || locked} onClick={() => setDraft(draftFromView(view))} data-cancel-lines="true">Cancel</button>
      </div>
      {error && <div className="eval-status eval-status-error eval-status-compact" role="alert" data-lines-error="true">{error}</div>}
      {savedNotEvaluated && <RetainedSaveNote />}
    </details>
  );
}
