import { useEffect, useState } from "react";
import { postProgramFacts } from "../api";
import { runEvaluation, useEvaluationRun } from "../lib/evaluationRun";
import { changedFacts, chooseBoolean, draftFrom, isDirty, validateDraft } from "../lib/programFacts";
import EvaluationStatus, { RetainedSaveNote } from "./EvaluationStatus";

// Producer-stated program facts (NA-RECONCILIATION-21): the Overview's one panel for the day counts, wages, approvals and eligibility statements the credits of British Columbia, Nova Scotia, New Brunswick,
// Saskatchewan, Montana and the federal CPTC cost base need. Groups, labels, bounds, exclusive pairs and the "Producer-stated" provenance all come from the served view (`production.program_facts`); nothing is
// defaulted here. A blank is Unknown (never zero), a yes/no statement can only be Yes (a No is never stored), and a number is checked against the served bounds before it is sent. Saving stores only the
// changed facts, then runs the shared single-flight evaluation exactly once (the control locks while a run is active); on a project whose results are retained from an earlier engine the facts are saved
// and no evaluation starts silently.
export default function ProgramFactsPanel({ projectId, programFacts, onSaved, evaluateOnSave = true }) {
  const [view, setView] = useState(programFacts);
  const [drafts, setDrafts] = useState({});
  const [savingGroup, setSavingGroup] = useState(null);
  const [error, setError] = useState(null);
  const [savedNotEvaluated, setSavedNotEvaluated] = useState(false);
  const run = useEvaluationRun(projectId);
  useEffect(() => { setView(programFacts); setDrafts({}); }, [programFacts]);       // a cold reload / refetch restores the stored values, discarding local drafts
  if (!projectId || !view?.groups) return null;

  const draftOf = (g) => drafts[g.id] ?? draftFrom(g);

  async function save(group) {
    const draft = draftOf(group);
    if (savingGroup || run.running) return;
    const errors = validateDraft(group, draft);
    if (Object.keys(errors).length) { setError("Fix the highlighted fields first."); return; }
    const { evidenced, amounts } = changedFacts(group, draft);
    setSavingGroup(group.id);
    setError(null);
    setSavedNotEvaluated(false);
    try {
      const saved = await postProgramFacts(projectId, { evidenced, amounts });
      if (saved?.program_facts) { setView(saved.program_facts); setDrafts((d) => { const { [group.id]: _gone, ...rest } = d; return rest; }); }
      if (evaluateOnSave) await runEvaluation(projectId);
      else setSavedNotEvaluated(true);
      onSaved?.();
    } catch (err) {
      setError((err && err.message) || "The program facts could not be saved.");
    } finally {
      setSavingGroup(null);
    }
  }

  return (
    <section className="pd-panel" data-testid="program-facts" data-program-facts-stated={view.stated_count}>
      <div className="pd-header">
        <span className="pd-title-row"><span className="pd-title">Program facts</span></span>
        <span className="pd-col-label">{view.stated_count ? `${view.stated_count} stated` : "None stated"}</span>
      </div>
      <div className="pd-extra-note text-tertiary">{view.note}</div>
      {view.groups.map((group) => {
        const draft = draftOf(group);
        const errors = validateDraft(group, draft);
        const dirty = isDirty(group, draft);
        return (
          <details key={group.id} className="pd-person" open={group.stated_count > 0} data-program-facts-group={group.id}>
            <summary className="pd-row">
              <span className="pd-ident"><span className="pd-role">{group.title}</span><span className="pd-name text-tertiary">{group.authority}</span></span>
              <span className="pd-col-label">{group.stated_count ? `${group.stated_count} stated` : "Unknown"}</span>
            </summary>
            {group.facts.map((f) => (
              <div key={f.key} className="pd-row" data-program-fact={f.key} data-fact-state={f.state}>
                <div className="pd-ident">
                  <span className="pd-role">{f.label}</span>
                  {f.help && <span className="pd-name text-tertiary">{f.help}</span>}
                  <span className="pd-name text-tertiary">Producer-stated · {f.state === "STATED" ? "Stated" : "Unknown"}</span>
                </div>
                {f.kind === "boolean" ? (
                  <select
                    className={`pd-select ${draft[f.key] === "yes" ? "" : "pd-missing"}`}
                    aria-label={f.label}
                    value={draft[f.key] ?? ""}
                    disabled={savingGroup !== null || run.running}
                    onChange={(e) => setDrafts((d) => ({ ...d, [group.id]: chooseBoolean(group, draftOf(group), f.key, e.target.value === "yes") }))}
                  >
                    <option value="">Unknown</option>
                    <option value="yes">Yes</option>
                  </select>
                ) : (
                  <input
                    className={`pd-select ${draft[f.key] ? "" : "pd-missing"}`}
                    aria-label={f.label}
                    inputMode="decimal"
                    placeholder="Unknown"
                    value={draft[f.key] ?? ""}
                    disabled={savingGroup !== null || run.running}
                    onChange={(e) => setDrafts((d) => ({ ...d, [group.id]: { ...draftOf(group), [f.key]: e.target.value } }))}
                    title={f.unit ? `${f.unit}` : undefined}
                  />
                )}
                {errors[f.key] && <span className="eval-status eval-status-error eval-status-compact" role="alert" data-fact-error={f.key}>{errors[f.key]}</span>}
              </div>
            ))}
            <div className="pd-row">
              <button type="button" className="ghost-action" disabled={!dirty || Object.keys(errors).length > 0 || savingGroup !== null || run.running} onClick={() => save(group)} data-save-group={group.id}>
                {savingGroup === group.id ? "Saving…" : "Save"}
              </button>
            </div>
          </details>
        );
      })}
      {error && <div className="eval-status eval-status-error eval-status-compact" role="alert" data-program-facts-error="true">{error}</div>}
      <EvaluationStatus projectId={projectId} onCompleted={onSaved} compact />
      {savedNotEvaluated && <RetainedSaveNote />}
    </section>
  );
}
