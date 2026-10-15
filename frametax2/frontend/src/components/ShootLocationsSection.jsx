import { useEffect, useState } from "react";
import { postShootLocations } from "../api";
import { runEvaluation, useEvaluationRun } from "../lib/evaluationRun";
import {
  BC_ZONES, CLASSIFICATIONS, CONFIDENCES, METHODS, ROLES, STATE_TEXT, blankDraft, consequencesFor, derivedRows, draftsFrom, hasErrors, isDirty, jurisdictionsOf, methodLabel,
  payloadFrom, resetProducerClassifications, suppliedRows, usedDays, validateDrafts,
} from "../lib/locations";
import { structurePrograms } from "../lib/resolvedRequirements";
import { RetainedSaveNote } from "./EvaluationStatus";

// Filming locations (NA-RECONCILIATION-24), a section of the Resolved Requirements panel (one fact system, one evaluation flow). A location is an explicit row: name, jurisdiction, city, county, shooting
// days, role (selected planning location or retained schedule location) and the classifications the system cannot derive yet, each with its source. Blank days are Unknown, not zero. What the system
// derives (a county class from an official list, an authority determination) is read-only with its provenance, apart from what the producer supplied. Save stores the list and runs the shared single-flight
// evaluation once (none for an unchanged list; none on a project whose results are retained from an earlier engine); Cancel restores the persisted list; Reset clears one location's producer-supplied
// classifications. Only the jurisdictions of the selected structure are offered.
export default function ShootLocationsSection({ projectId, view, structure, onSaved, evaluateOnSave = true }) {
  const [shown, setShown] = useState(view);
  const [drafts, setDrafts] = useState(() => draftsFrom(view));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedNotEvaluated, setSavedNotEvaluated] = useState(false);
  const run = useEvaluationRun(projectId);
  useEffect(() => { setShown(view); setDrafts(draftsFrom(view)); }, [view]);       // a cold reload / refetch restores the persisted list, discarding local edits
  const programs = structurePrograms(structure);
  const jurisdictions = jurisdictionsOf(programs);
  if (!projectId || !shown || !jurisdictions.length) return null;

  const total = shown.total_days ?? null;
  const errors = validateDrafts(drafts, total);
  const dirty = isDirty(drafts, shown);
  const locked = saving || run.running;
  const byId = new Map((shown.locations ?? []).map((l) => [l.id, l]));
  const consequences = consequencesFor(shown, programs);
  const mine = drafts.filter((d) => jurisdictions.includes(d.jurisdiction_code));
  const set = (id, patch) => setDrafts((all) => all.map((d) => (d.id === id ? { ...d, ...patch } : d)));
  const setAttr = (id, name, value) => setDrafts((all) => all.map((d) => (d.id === id ? { ...d, attrs: { ...d.attrs, [name]: value } } : d)));

  async function save() {
    if (saving || run.running) return;
    if (hasErrors(errors)) { setError("Fix the highlighted fields first."); return; }
    setSaving(true);
    setError(null);
    setSavedNotEvaluated(false);
    try {
      const saved = await postShootLocations(projectId, payloadFrom(drafts));
      if (saved?.shoot_locations) { setShown(saved.shoot_locations); setDrafts(draftsFrom(saved.shoot_locations)); }
      if (evaluateOnSave) await runEvaluation(projectId);
      else setSavedNotEvaluated(true);
      onSaved?.();
    } catch (err) {
      setError((err && err.message) || "The locations could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  const field = (d, key, label, input) => (
    <label className="pd-name" key={key}>
      <span className="text-tertiary">{label}</span>
      {input}
      {errors[d.id]?.[key] && <span className="eval-status eval-status-error eval-status-compact" role="alert" data-location-error={`${d.id}:${key}`}>{errors[d.id][key]}</span>}
    </label>
  );

  return (
    <details className="pd-person" open data-testid="shoot-locations" data-requirements-section="locations">
      <summary className="pd-row">
        <span className="pd-ident"><span className="pd-role">Filming locations</span><span className="pd-name text-tertiary">Locality is never inferred from the jurisdiction: enter each location</span></span>
        <span className="pd-col-label" data-location-days={usedDays(drafts)}>{usedDays(drafts)}{total !== null ? ` of ${total}` : ""} days placed</span>
      </summary>
      {errors._all?.days && <div className="eval-status eval-status-error eval-status-compact" role="alert" data-location-error="_all">{errors._all.days}</div>}
      {mine.length === 0 && <div className="pd-row" data-location-empty="true"><div className="pd-ident"><span className="pd-name text-tertiary">No location entered. Unknown locations keep the conditional upside and name what is needed.</span></div></div>}
      {mine.map((d) => {
        const persisted = byId.get(d.id);
        const derived = persisted ? derivedRows(persisted) : [];
        const supplied = persisted ? suppliedRows(persisted) : [];
        const unresolved = persisted ? Object.entries(persisted.unresolved ?? {}) : [];
        const specs = CLASSIFICATIONS[d.jurisdiction_code] ?? [];
        return (
          <div key={d.id} className="pd-row rr-location" data-location={d.id} data-location-jurisdiction={d.jurisdiction_code}>
            <div className="pd-ident">
              {field(d, "label", "Name", <input className="pd-select" aria-label="Location name" value={d.label} disabled={locked} onChange={(e) => set(d.id, { label: e.target.value })} />)}
              <label className="pd-name"><span className="text-tertiary">Role</span>
                <select className="pd-select" aria-label="Location role" value={d.role} disabled={locked} onChange={(e) => set(d.id, { role: e.target.value })}>{ROLES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select></label>
              <label className="pd-name"><span className="text-tertiary">Jurisdiction</span>
                <select className="pd-select" aria-label="Location jurisdiction" value={d.jurisdiction_code} disabled={locked} onChange={(e) => set(d.id, { jurisdiction_code: e.target.value, attrs: {} })}>
                  {[...new Set([...jurisdictions, d.jurisdiction_code])].map((j) => <option key={j} value={j}>{j}</option>)}</select></label>
              <label className="pd-name"><span className="text-tertiary">City</span><input className="pd-select" aria-label="City" value={d.city} disabled={locked} onChange={(e) => set(d.id, { city: e.target.value })} /></label>
              <label className="pd-name"><span className="text-tertiary">County</span><input className="pd-select" aria-label="County" value={d.county} disabled={locked} onChange={(e) => set(d.id, { county: e.target.value })} /></label>
              {field(d, "days", "Shoot days (blank = Unknown)", <input className={`pd-select ${d.days === "" ? "pd-missing" : ""}`} aria-label="Shoot days" inputMode="numeric" placeholder="Unknown" value={d.days} disabled={locked} onChange={(e) => set(d.id, { days: e.target.value })} />)}
              {derived.map((r) => (
                <span key={r.key} className="pd-name rr-prov-verified rr-fact" data-derived-classification={r.key} data-provenance="DERIVED">
                  {r.key === "county_class" ? `County class ${r.value}` : `${r.key}: ${String(r.value)}`} · {methodLabel(r.method)} · {r.source}{r.version ? ` (${r.version})` : ""}
                </span>
              ))}
              {supplied.map((r) => (
                <span key={r.key} className="pd-name rr-prov-producer_stated rr-fact" data-supplied-classification={r.key} data-provenance="PRODUCER_STATED">
                  {r.key}: {String(r.value)} · {methodLabel(r.method)} · {r.source}{r.version ? ` (${r.version})` : ""}
                </span>
              ))}
              {unresolved.map(([k, why]) => <span key={k} className="pd-name rr-needed" data-location-unresolved={k}>Needed ({k.replace(/_/g, " ")}): {why}</span>)}
              {specs.map((spec) => field(d, spec.name, `${spec.label} - producer-supplied`,
                spec.kind === "boolean" ? (
                  <select className="pd-select" aria-label={spec.label} value={d.attrs[spec.name] ?? ""} disabled={locked} onChange={(e) => setAttr(d.id, spec.name, e.target.value)}>
                    <option value="">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select>
                ) : spec.kind === "zone" ? (
                  <select className="pd-select" aria-label={spec.label} value={d.attrs[spec.name] ?? ""} disabled={locked} onChange={(e) => setAttr(d.id, spec.name, e.target.value)}>
                    <option value="">Unknown</option>{BC_ZONES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select>
                ) : (
                  <input className="pd-select" aria-label={spec.label} placeholder="Unknown" inputMode={spec.kind === "number" ? "decimal" : "text"} value={d.attrs[spec.name] ?? ""} disabled={locked}
                    onChange={(e) => setAttr(d.id, spec.name, e.target.value)} />
                )))}
              {specs.some((s) => String(d.attrs[s.name] ?? "").trim() !== "") && (
                <span className="pd-name" data-location-source={d.id}>
                  {field(d, "source", "Source of what you supplied", <input className="pd-select" aria-label="Source" value={d.source} disabled={locked} onChange={(e) => set(d.id, { source: e.target.value })} />)}
                  <label className="pd-name"><span className="text-tertiary">Method</span>
                    <select className="pd-select" aria-label="Source method" value={d.method} disabled={locked} onChange={(e) => set(d.id, { method: e.target.value })}>{METHODS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select></label>
                  <label className="pd-name"><span className="text-tertiary">Confidence</span>
                    <select className="pd-select" aria-label="Source confidence" value={d.confidence} disabled={locked} onChange={(e) => set(d.id, { confidence: e.target.value })}>{CONFIDENCES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select></label>
                  <label className="pd-name"><span className="text-tertiary">Source or version date</span>
                    <input className="pd-select" aria-label="Source date" placeholder="YYYY-MM-DD" value={d.effective_date} disabled={locked} onChange={(e) => set(d.id, { effective_date: e.target.value })} /></label>
                </span>
              )}
            </div>
            <span>
              <button type="button" className="ghost-action" disabled={locked} onClick={() => set(d.id, resetProducerClassifications(d))} data-reset-location={d.id}>Reset classifications</button>
              <button type="button" className="ghost-action" disabled={locked} onClick={() => setDrafts((all) => all.filter((x) => x.id !== d.id))} data-remove-location={d.id}>Remove</button>
            </span>
          </div>
        );
      })}
      <div className="pd-row">
        {jurisdictions.map((j) => (
          <button key={j} type="button" className="ghost-action" disabled={locked} onClick={() => setDrafts((all) => [...all, blankDraft(j)])} data-add-location={j}>Add {j} location</button>
        ))}
        <button type="button" className="ghost-action" disabled={!dirty || hasErrors(errors) || locked} onClick={save} data-save-locations="true">{saving ? "Saving…" : "Save locations"}</button>
        <button type="button" className="ghost-action" disabled={!dirty || locked} onClick={() => setDrafts(draftsFrom(shown))} data-cancel-locations="true">Cancel</button>
      </div>
      {consequences.length > 0 && (
        <div className="pd-row" data-location-consequences="true">
          <div className="pd-ident">
            <span className="pd-role">What these locations do to the price</span>
            {consequences.map((c) => (
              <span key={c.predicate} className={`pd-name rr-state rr-state-${c.state.toLowerCase()}`} data-consequence={c.predicate} data-consequence-state={c.state}>
                {c.label}: {STATE_TEXT[c.state]} · {c.effects.map((e) => e.text).join(" · ")}
              </span>
            ))}
          </div>
        </div>
      )}
      {error && <div className="eval-status eval-status-error eval-status-compact" role="alert" data-locations-error="true">{error}</div>}
      {savedNotEvaluated && <RetainedSaveNote />}
    </details>
  );
}
