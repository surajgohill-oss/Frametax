import { useState } from "react";
import { postProductionType } from "../api";
import { runEvaluation, useEvaluationRun } from "../lib/evaluationRun";
import EvaluationStatus, { RetainedSaveNote } from "./EvaluationStatus";

// Production type — the Overview's one control for the producer's stated type (feature / series / documentary / animation). It is the project's saved format, mapped by the backend to the
// production type the statutory rules are scoped by, so choosing a type changes WHICH programs can price (most US state programs are scoped to feature films), not a display label. The
// options, labels, the effective type and the "not stated" disclosure all come from the served view (`production.production_type`); nothing is defaulted here. Choosing saves the type, then runs
// the shared single-flight evaluation (the same wrapper every producer-input save uses), so the real running / completed / failed state shows and the control locks while a run is active. On a project
// whose results are retained from an earlier engine the type is saved and no evaluation starts silently.
export default function ProductionTypeLine({ projectId, productionType, onSaved, evaluateOnSave = true }) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedNotEvaluated, setSavedNotEvaluated] = useState(false);
  const run = useEvaluationRun(projectId);
  if (!projectId || !productionType) return null;

  async function choose(e) {
    const format = e.target.value === "" ? null : e.target.value;
    if (saving || run.running) return;
    setSaving(true);
    setError(null);
    try {
      await postProductionType(projectId, format);
      if (evaluateOnSave) await runEvaluation(projectId);
      else setSavedNotEvaluated(true);
      onSaved?.();
    } catch (err) {
      setError((err && err.message) || "The production type could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  const stated = productionType.state === "STATED";
  return (
    <section className="pd-panel" data-testid="production-type" data-production-type-state={productionType.state}>
      <div className="pd-header">
        <span className="pd-title-row"><span className="pd-title">Production type</span></span>
        <span className="pd-col-label">{stated ? "Stated" : "Not stated"}</span>
      </div>
      <div className="pd-person">
        <div className="pd-row">
          <div className="pd-ident">
            <span className="pd-role">Type</span>
            <span className="pd-name">
              {stated ? (productionType.options.find((o) => o.format === productionType.format)?.label ?? productionType.format) : <span className="text-tertiary">Not stated</span>}
            </span>
          </div>
          <select
            className={`pd-select ${stated ? "" : "pd-missing"}`}
            aria-label="Production type"
            value={productionType.format ?? ""}
            disabled={saving || run.running}
            onChange={choose}
          >
            <option value="">— not stated</option>
            {productionType.options.map((o) => (
              <option key={o.format} value={o.format}>{o.label}</option>
            ))}
          </select>
        </div>
        <div className="pd-extra-note text-tertiary" title={`Effective production type: ${productionType.effective_production_type}`}>{productionType.note}</div>
      </div>
      {error && <div className="eval-status eval-status-error eval-status-compact" role="alert" data-production-type-error="true">{error}</div>}
      <EvaluationStatus projectId={projectId} onCompleted={onSaved} compact />
      {savedNotEvaluated && <RetainedSaveNote />}
    </section>
  );
}
