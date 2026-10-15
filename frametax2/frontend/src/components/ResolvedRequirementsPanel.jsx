import { useEffect, useState } from "react";
import { postProgramFacts } from "../api";
import { runEvaluation, useEvaluationRun } from "../lib/evaluationRun";
import {
  booleanOptions, changedFacts, chooseBoolean, draftFrom, factStatusText, isDirty, isReadOnly, ladderLines, provenanceLabel, stillNeeded, validateDraft,
} from "../lib/resolvedRequirements";
import EvaluationStatus, { RetainedSaveNote } from "./EvaluationStatus";

// Resolved requirements (NA-RECONCILIATION-22). One value and one provenance per fact, resolved by a fixed precedence in the backend (verified evidence, then a producer statement, then a scenario
// assumption, then Unknown). A fact the engine derives (from the schedule, the budget or the selected scenario) is shown read-only with where it came from; a control appears only for a genuine producer
// decision or for evidence the system does not hold. Yes / No / Unknown are three different answers: Unknown keeps the conditional potential, No applies the rule's failed treatment. Saving stores only the
// changed facts, then runs the shared single-flight evaluation exactly once (the control locks while a run is active); on a project whose results are retained from an earlier engine the facts are saved
// and no evaluation starts silently. Nothing here is defaulted: labels, groups, bounds, provenance, requirements and the Missouri ladder all come from the served view.
export default function ResolvedRequirementsPanel({ projectId, programFacts, onSaved, evaluateOnSave = true }) {
  const [view, setView] = useState(programFacts);
  const [drafts, setDrafts] = useState({});
  const [savingGroup, setSavingGroup] = useState(null);
  const [error, setError] = useState(null);
  const [savedNotEvaluated, setSavedNotEvaluated] = useState(false);
  const run = useEvaluationRun(projectId);
  useEffect(() => { setView(programFacts); setDrafts({}); }, [programFacts]);       // a cold reload / refetch restores the stored values, discarding local drafts
  if (!projectId || !view?.groups) return null;

  const draftOf = (g) => drafts[g.id] ?? draftFrom(g);
  const needed = stillNeeded(view);
  const locked = savingGroup !== null || run.running;

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
      setError((err && err.message) || "The requirements could not be saved.");
    } finally {
      setSavingGroup(null);
    }
  }

  return (
    <section className="pd-panel" data-testid="resolved-requirements" data-resolved-count={view.resolved_count} data-needed-count={needed.length}>
      <div className="pd-header">
        <span className="pd-title-row"><span className="pd-title">Resolved requirements</span></span>
        <span className="pd-col-label">{view.resolved_count} resolved · {needed.length} still needed</span>
      </div>
      <div className="pd-extra-note text-tertiary">{view.note}</div>
      {view.missouri && (
        <div className="pd-row rr-ladder" data-ladder="missouri">
          <div className="pd-ident">
            <span className="pd-role">Missouri rate</span>
            {ladderLines(view.missouri).map((l) => (
              <span key={l.id} className={`pd-name rr-state rr-state-${String(l.state).toLowerCase()}`} data-ladder-step={l.id} data-ladder-state={l.state}>
                {l.text}{l.state === "TRUE" || l.state === "TOTAL" ? "" : ` · ${l.state === "FALSE" ? "No" : "Unknown"}`}
              </span>
            ))}
          </div>
        </div>
      )}
      {view.scenario_rules?.length > 0 && (
        <details className="pd-person" data-scenario-rules="true">
          <summary className="pd-row"><span className="pd-ident"><span className="pd-role">What the selected scenario establishes on its own</span></span></summary>
          {view.scenario_rules.map((r) => (
            <div key={`${r.program}:${r.fact_key}`} className="pd-row" data-scenario-rule={r.fact_key}>
              <div className="pd-ident"><span className="pd-role">{r.rule}</span><span className="pd-name text-tertiary">{provenanceLabel("SCENARIO_ASSUMED")} · {r.authority}</span></div>
            </div>
          ))}
        </details>
      )}
      {view.groups.map((group) => {
        const draft = draftOf(group);
        const errors = validateDraft(group, draft);
        const dirty = isDirty(group, draft);
        const editable = group.facts.some((f) => !isReadOnly(f));
        const open = group.facts.some((f) => f.state === "UNKNOWN" && !isReadOnly(f)) || group.resolved_count > 0;
        return (
          <details key={group.id} className="pd-person" open={open && group.resolved_count > 0} data-requirements-group={group.id}>
            <summary className="pd-row">
              <span className="pd-ident"><span className="pd-role">{group.title}</span><span className="pd-name text-tertiary">{group.authority}</span></span>
              <span className="pd-col-label">{group.resolved_count} of {group.facts.length} resolved</span>
            </summary>
            {group.facts.map((f) => (
              <div key={f.key} className={`pd-row rr-fact rr-prov-${String(f.provenance).toLowerCase()}`} data-requirement={f.key} data-fact-state={f.state} data-provenance={f.provenance} data-read-only={isReadOnly(f) ? "true" : "false"}>
                <div className="pd-ident">
                  <span className="pd-role">{f.label}</span>
                  {f.help && <span className="pd-name text-tertiary">{f.help}</span>}
                  {f.effects?.length > 0 && <span className="pd-name text-tertiary" data-fact-effects="true">{f.effects.join(" · ")}</span>}
                  <span className="pd-name text-tertiary rr-provenance">{provenanceLabel(f.provenance)} · {factStatusText(f)}{f.basis ? ` · ${f.basis}` : ""}</span>
                  {f.conflict && <span className="pd-name rr-conflict" role="status" data-fact-conflict={f.key}>{f.conflict}</span>}
                  {f.scenario_rule && <span className="pd-name text-tertiary">{f.scenario_rule}</span>}
                  {f.state === "UNKNOWN" && !isReadOnly(f) && <span className="pd-name rr-needed" data-fact-needed={f.key}>Needed: {f.requirement ?? f.label}</span>}
                </div>
                {isReadOnly(f) ? (
                  <span className="pd-col-label rr-readonly" data-fact-readonly={f.key}>{factStatusText(f)}</span>
                ) : f.kind === "number" ? (
                  <input
                    className={`pd-select ${draft[f.key] ? "" : "pd-missing"}`}
                    aria-label={f.label}
                    inputMode="decimal"
                    placeholder="Unknown"
                    value={draft[f.key] ?? ""}
                    disabled={locked}
                    onChange={(e) => setDrafts((d) => ({ ...d, [group.id]: { ...draftOf(group), [f.key]: e.target.value } }))}
                    title={f.unit ? `${f.unit}` : undefined}
                  />
                ) : (
                  <select
                    className={`pd-select ${draft[f.key] ? "" : "pd-missing"}`}
                    aria-label={f.label}
                    value={draft[f.key] ?? ""}
                    disabled={locked}
                    onChange={(e) => setDrafts((d) => ({ ...d, [group.id]: chooseBoolean(group, draftOf(group), f.key, e.target.value) }))}
                  >
                    <option value="">Unknown</option>
                    <option value="yes">Yes</option>
                    {booleanOptions(f).includes("no") && <option value="no">No</option>}
                  </select>
                )}
                {errors[f.key] && <span className="eval-status eval-status-error eval-status-compact" role="alert" data-fact-error={f.key}>{errors[f.key]}</span>}
              </div>
            ))}
            {editable && (
              <div className="pd-row">
                <button type="button" className="ghost-action" disabled={!dirty || Object.keys(errors).length > 0 || locked} onClick={() => save(group)} data-save-group={group.id}>
                  {savingGroup === group.id ? "Saving…" : "Save"}
                </button>
              </div>
            )}
          </details>
        );
      })}
      {error && <div className="eval-status eval-status-error eval-status-compact" role="alert" data-requirements-error="true">{error}</div>}
      <EvaluationStatus projectId={projectId} onCompleted={onSaved} compact />
      {savedNotEvaluated && <RetainedSaveNote />}
    </section>
  );
}
