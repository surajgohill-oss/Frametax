import { useEffect, useState } from "react";
import { postProgramFacts } from "../api";
import { runEvaluation, useEvaluationRun } from "../lib/evaluationRun";
import {
  SECTION_ORDER, SECTION_TITLE, booleanOptions, changedFacts, chooseBoolean, draftFrom, factStatusText, hasMissouri, isDirty, isReadOnly, ladderLines, provenanceLabel,
  relevantLocationNeeds, relevantScenarioRules, sectionsFor, structureLadder, structureUpside, validateDraft,
} from "../lib/resolvedRequirements";
import EvaluationStatus, { RetainedSaveNote } from "./EvaluationStatus";
import LineInputsSection from "./LineInputsSection";
import ShootLocationsSection from "./ShootLocationsSection";

// Resolved requirements (NA-RECONCILIATION-22, scoped to the selected structure in NA-RECONCILIATION-23). One value and one provenance per fact, resolved by a fixed precedence in the backend (verified evidence, then a producer statement, then a scenario
// assumption, then Unknown). A fact the engine derives (from the schedule, the budget or the selected scenario) is shown read-only with where it came from; a control appears only for a genuine producer
// decision or for evidence the system does not hold. Yes / No / Unknown are three different answers: Unknown keeps the conditional potential, No applies the rule's failed treatment. Saving stores only the
// changed facts, then runs the shared single-flight evaluation exactly once (the control locks while a run is active); on a project whose results are retained from an earlier engine the facts are saved
// and no evaluation starts silently. Nothing here is defaulted: labels, groups, bounds, provenance, requirements and the Missouri ladder all come from the served view.
export default function ResolvedRequirementsPanel({ projectId, programFacts, shootLocations, structure, onSaved, evaluateOnSave = true }) {
  const [view, setView] = useState(programFacts);
  const [draft, setDraft] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedNotEvaluated, setSavedNotEvaluated] = useState(false);
  const run = useEvaluationRun(projectId);
  useEffect(() => { setView(programFacts); setDraft(null); }, [programFacts]);       // a cold reload / refetch restores the stored values, discarding local drafts
  if (!projectId || !view?.groups) return null;

  const sections = sectionsFor(view, structure);
  const editable = SECTION_ORDER.flatMap((k) => sections[k]).filter((f) => !isReadOnly(f));
  const scope = { facts: editable };                                           // one flat scope: only the relevant, editable facts of the selected structure
  const current = draft ?? draftFrom(scope);
  const errors = validateDraft(scope, current);
  const dirty = isDirty(scope, current);
  const locked = saving || run.running;
  const upside = structureUpside(structure);
  const needs = relevantLocationNeeds(view, structure);
  const total = SECTION_ORDER.reduce((n, k) => n + sections[k].length, 0);

  async function save() {
    if (saving || run.running) return;
    if (Object.keys(errors).length) { setError("Fix the highlighted fields first."); return; }
    const { evidenced, amounts } = changedFacts(scope, current);
    setSaving(true);
    setError(null);
    setSavedNotEvaluated(false);
    try {
      const saved = await postProgramFacts(projectId, { evidenced, amounts });
      if (saved?.program_facts) { setView(saved.program_facts); setDraft(null); }
      if (evaluateOnSave) await runEvaluation(projectId);
      else setSavedNotEvaluated(true);
      onSaved?.();
    } catch (err) {
      setError((err && err.message) || "The requirements could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  const control = (f) => (isReadOnly(f) ? (
    <span className="pd-col-label rr-readonly" data-fact-readonly={f.key}>{factStatusText(f)}</span>
  ) : f.kind === "number" ? (
    <input
      className={`pd-select ${current[f.key] ? "" : "pd-missing"}`}
      aria-label={f.label}
      inputMode="decimal"
      placeholder="Unknown"
      value={current[f.key] ?? ""}
      disabled={locked}
      onChange={(e) => setDraft({ ...current, [f.key]: e.target.value })}
      title={f.unit ? `${f.unit}` : undefined}
    />
  ) : (
    <select
      className={`pd-select ${current[f.key] ? "" : "pd-missing"}`}
      aria-label={f.label}
      value={current[f.key] ?? ""}
      disabled={locked}
      onChange={(e) => setDraft(chooseBoolean(scope, current, f.key, e.target.value))}
    >
      <option value="">Unknown</option>
      <option value="yes">Yes</option>
      {booleanOptions(f).includes("no") && <option value="no">No</option>}
    </select>
  ));

  const row = (f) => (
    <div key={f.key} className={`pd-row rr-fact rr-prov-${String(f.provenance).toLowerCase()}`} data-requirement={f.key} data-fact-state={f.state} data-provenance={f.provenance} data-read-only={isReadOnly(f) ? "true" : "false"}>
      <div className="pd-ident">
        <span className="pd-role">{f.label}</span>
        {f.help && <span className="pd-name text-tertiary">{f.help}</span>}
        {f.effects?.length > 0 && <span className="pd-name text-tertiary" data-fact-effects="true">{f.effects.join(" · ")}</span>}
        <span className="pd-name text-tertiary rr-provenance">{provenanceLabel(f.provenance)} · {factStatusText(f)}{f.basis ? ` · ${f.basis}` : ""}</span>
        {f.category === "FAILED" && <span className="pd-name rr-conflict" data-fact-failure={f.key}>Not met: {f.failure_effect}</span>}
        {f.conflict && <span className="pd-name rr-conflict" role="status" data-fact-conflict={f.key}>{f.conflict}</span>}
        {f.state === "UNKNOWN" && <span className="pd-name rr-needed" data-fact-needed={f.key}>{f.category === "EXTERNAL_APPROVAL" ? "Approval needed" : "Needed"}: {f.requirement ?? f.label}</span>}
      </div>
      {control(f)}
      {errors[f.key] && <span className="eval-status eval-status-error eval-status-compact" role="alert" data-fact-error={f.key}>{errors[f.key]}</span>}
    </div>
  );

  return (
    <section className="pd-panel" data-testid="resolved-requirements" data-relevant-count={total}>
      <div className="pd-header">
        <span className="pd-title-row"><span className="pd-title">Resolved requirements</span></span>
        <span className="pd-col-label">{structure ? `${total} for this structure` : "Select a structure"}</span>
      </div>
      <div className="pd-extra-note text-tertiary">{view.note}</div>
      {hasMissouri(structure) && view.missouri && (
        <div className="pd-row rr-ladder" data-ladder="missouri">
          <div className="pd-ident">
            <span className="pd-role">Missouri rate</span>
            {ladderLines(structureLadder(view, structure)).map((l) => (
              <span key={l.id} className={`pd-name rr-state rr-state-${String(l.state).toLowerCase()}`} data-ladder-step={l.id} data-ladder-state={l.state}>
                {l.text}{l.state === "TRUE" || l.state === "TOTAL" ? "" : ` · ${l.state === "FALSE" ? "No" : "Unknown"}`}
              </span>
            ))}
          </div>
        </div>
      )}
      {needs.length > 0 && (
        <div className="pd-row" data-location-needs="true">
          <div className="pd-ident"><span className="pd-role">Filming locations needed</span>
            {needs.map((n) => <span key={n.key} className="pd-name rr-needed" data-location-need={n.key}>{n.requirement}</span>)}
          </div>
        </div>
      )}
      <ShootLocationsSection projectId={projectId} view={shootLocations} structure={structure} onSaved={onSaved} evaluateOnSave={evaluateOnSave} />
      <LineInputsSection projectId={projectId} structure={structure} refreshKey={programFacts} onSaved={onSaved} evaluateOnSave={evaluateOnSave} />
      {SECTION_ORDER.map((k) => {
        const list = sections[k];
        if (!list.length && !(k === "upside" && upside.length)) return null;
        return (
          <details key={k} className="pd-person" open={k !== "satisfied"} data-requirements-section={k}>
            <summary className="pd-row">
              <span className="pd-ident"><span className="pd-role">{SECTION_TITLE[k]}</span></span>
              <span className="pd-col-label">{list.length}</span>
            </summary>
            {k === "upside" && upside.map((u) => (
              <div key={u.id} className="pd-row" data-structure-upside={u.id}>
                <div className="pd-ident"><span className="pd-role">{u.description}</span><span className="pd-name text-tertiary">Unlocks ${Math.round(u.usd).toLocaleString()} in this structure{u.note ? ` · ${u.note}` : ""}</span></div>
              </div>
            ))}
            {list.map(row)}
          </details>
        );
      })}
      {relevantScenarioRules(view, structure).length > 0 && (
        <details className="pd-person" data-scenario-rules="true">
          <summary className="pd-row"><span className="pd-ident"><span className="pd-role">What this scenario establishes on its own</span></span></summary>
          {relevantScenarioRules(view, structure).map((r) => (
            <div key={`${r.program}:${r.fact_key}`} className="pd-row" data-scenario-rule={r.fact_key}>
              <div className="pd-ident"><span className="pd-role">{r.rule}</span><span className="pd-name text-tertiary">{provenanceLabel("SCENARIO_ASSUMED")} · {r.authority}</span></div>
            </div>
          ))}
        </details>
      )}
      {editable.length > 0 && (
        <div className="pd-row">
          <button type="button" className="ghost-action" disabled={!dirty || Object.keys(errors).length > 0 || locked} onClick={save} data-save-requirements="true">
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      )}
      {error && <div className="eval-status eval-status-error eval-status-compact" role="alert" data-requirements-error="true">{error}</div>}
      <EvaluationStatus projectId={projectId} onCompleted={onSaved} compact />
      {savedNotEvaluated && <RetainedSaveNote />}
    </section>
  );
}
