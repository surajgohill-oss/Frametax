import { useState } from "react";
import { postPeople } from "../api";

// Production Facts — approved Overview left column. This panel is the
// Overview representation of the SAME Production Record the Workspace
// Inspector edits: rows use the real backend contract (POST /people,
// role-level nationality overrides — the backend's own model), so an edit
// here and an edit in Workspace hit the identical record. No duplicate
// input model, no second intake system.
//
// Nationality/Citizenship is the canonical recurring qualification identity
// the optimizer consumes across jurisdictions (cultural tests, treaty
// composition, cast/crew rules). Residency is deliberately NOT shown here
// per the approved design. No country-specific cultural-test inputs are
// recreated here. The backend tracks no Editor role, so none is shown.
//
// Flow: values discovered from uploads/state are shown; missing values are
// highlighted; completing one POSTs to /people and the optimizer recomputes
// on the refetch.

const NATIONALITIES = [
  ["GB", "British"], ["US", "American"], ["FR", "French"], ["DE", "German"],
  ["IT", "Italian"], ["ES", "Spanish"], ["IE", "Irish"], ["MT", "Maltese"],
  ["MU", "Mauritian"], ["FJ", "Fijian"], ["AU", "Australian"], ["NZ", "New Zealander"],
  ["CA", "Canadian"], ["IN", "Indian"], ["ZA", "South African"],
];

function NationalitySelect({ value, onChange, disabled, saving, missing, title }) {
  const known = NATIONALITIES.some(([code]) => code === value);
  return (
    <select
      className={`pd-select ${missing ? "pd-missing" : ""}`}
      value={value || ""}
      disabled={disabled || saving}
      title={title}
      onChange={(e) => onChange(e.target.value || null)}
    >
      <option value="">—</option>
      {!known && value && <option value={value}>{value}</option>}
      {NATIONALITIES.map(([code, label]) => (
        <option key={code} value={code}>{label}</option>
      ))}
    </select>
  );
}

// One fact row: role label, discovered name(s), and the single recurring
// qualification fact (nationality). Rows without a backend person record
// (Lead Cast 2/3 until cast is announced) render an honest disabled control
// rather than an input that could not persist.
function FactRow({ label, name, value, roleKey, onSaved }) {
  const [saving, setSaving] = useState(false);
  const editable = !!roleKey;

  async function save(code) {
    setSaving(true);
    try {
      await postPeople({ [`${roleKey}_nationality`]: code });
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="pd-person">
      <div className="pd-row">
        <div className="pd-ident">
          <span className="pd-role">{label}</span>
          <span className="pd-name">
            {name || <span className="text-tertiary">Not yet named</span>}
          </span>
        </div>
        <NationalitySelect
          value={value}
          onChange={save}
          disabled={!editable}
          saving={saving}
          missing={editable && !value}
          title={editable ? undefined : "No person record yet — nationality becomes editable once this cast member is added to the record"}
        />
      </div>
    </div>
  );
}

// Production Requirements — script-derived physical requirements (NOT
// selected jurisdictions). Auto-populated from the real script analysis
// (production.physical_requirements.script_requirements); each chip's
// tooltip carries the actual evidence line. These same flags already drive
// the optimizer's territory physical matching (territory_physical_match).
// No backend write path exists for these yet, so they are display-only —
// no fake edit control is rendered.
const REQ_LABELS = {
  marine: "Marine / Open water",
  open_water_filming: "Open-water filming",
  underwater_photography: "Underwater",
  period: "Historic / Period",
  night_work: "Night work",
  city: "Urban / City",
  desert: "Desert",
  snow: "Snow",
  animals: "Animals",
  vehicles: "Vehicle action",
  crowds: "Crowds",
};

function ProductionRequirements({ requirements }) {
  const sreq = requirements?.script_requirements || {};
  const entries = Object.entries(sreq)
    .filter(([k]) => REQ_LABELS[k])
    .sort(([, a], [, b]) => (b?.value === true ? 1 : 0) - (a?.value === true ? 1 : 0));

  return (
    <div className="pd-locations">
      <div className="pd-section-label">Production requirements</div>
      <p className="pd-req-note">Derived from script analysis · drives territory matching</p>
      {entries.length === 0 ? (
        <p className="pd-loc-empty">No script analysis available yet.</p>
      ) : (
        <div className="tag-row">
          {entries.map(([k, v]) => (
            <span
              key={k}
              className={`tag ${v?.value === true ? "active" : ""}`}
              title={v?.evidence || "Not evident in the material read"}
            >
              {REQ_LABELS[k]}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

const namesOf = (arr) => (arr || []).map((p) => p.name).filter(Boolean).join(", ");

export default function ProductionDetails({ people, requirements, refetch }) {
  const overrides = people?.overrides || {};
  const cast = people?.cast || [];
  const natOf = (roleKey, person) => overrides[roleKey]?.nationality || person?.nationality || "";

  return (
    <section className="pd-panel">
      <div className="pd-header">
        <span className="pd-title">Production facts</span>
        <span className="pd-col-label">Nationality</span>
      </div>

      <FactRow label="Writer" roleKey="writer" name={namesOf(people.writers)}
        value={natOf("writer", people.writers?.[0])} onSaved={refetch} />
      <FactRow label="Director" roleKey="director" name={namesOf(people.directors)}
        value={natOf("director", people.directors?.[0])} onSaved={refetch} />
      <FactRow label="Producers" roleKey="producer" name={namesOf(people.producers)}
        value={natOf("producer", people.producers?.[0])} onSaved={refetch} />
      <FactRow label="Lead Cast 1" roleKey="lead_cast" name={cast[0]?.name}
        value={natOf("lead_cast", cast[0])} onSaved={refetch} />
      <FactRow label="Lead Cast 2" roleKey={null} name={cast[1]?.name}
        value={cast[1]?.nationality || ""} onSaved={refetch} />
      <FactRow label="Lead Cast 3" roleKey={null} name={cast[2]?.name}
        value={cast[2]?.nationality || ""} onSaved={refetch} />

      <ProductionRequirements requirements={requirements} />
    </section>
  );
}
