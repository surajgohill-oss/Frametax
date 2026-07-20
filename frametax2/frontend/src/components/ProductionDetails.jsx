import { useState } from "react";
import { postPeople, postLocations } from "../api";
import { PERSON_ROLES } from "../lib/personRoles";

// Production Facts — approved Overview left column. This panel is the
// Overview representation of the SAME canonical Production Record the
// Workspace Inputs panel edits (POST /people role-level overrides — the
// backend's own model; both surfaces render from the shared PERSON_ROLES
// schema, so they can never diverge). Discovery (script/budget/upload
// extraction) supplies names where it found them; every name and every
// nationality/citizenship stays user-editable — including the unnamed
// lead-cast slots. Missing values are highlighted, and every edit
// invalidates the backend state so the Question Engine and optimizer
// recompute from the same record. Residency is deliberately NOT shown
// here per the approved design; no country-specific cultural-test
// interface is recreated — these are the reusable personnel facts the
// jurisdiction rule engines consume downstream.

const NATIONALITIES = [
  ["GB", "British"], ["US", "American"], ["FR", "French"], ["DE", "German"],
  ["IT", "Italian"], ["ES", "Spanish"], ["IE", "Irish"], ["MT", "Maltese"],
  ["MU", "Mauritian"], ["FJ", "Fijian"], ["AU", "Australian"], ["NZ", "New Zealander"],
  ["CA", "Canadian"], ["IN", "Indian"], ["ZA", "South African"],
];

function NationalitySelect({ value, onChange, saving, missing }) {
  const known = NATIONALITIES.some(([code]) => code === value);
  return (
    <select
      className={`pd-select ${missing ? "pd-missing" : ""}`}
      value={value || ""}
      disabled={saving}
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

// One fact row: role label, editable name, editable nationality. The name
// input commits on blur/Enter when changed (empty clears the override,
// returning to the discovered value); nationality commits on select.
function FactRow({ role, people, overrides, onSaved }) {
  const entries = people[role.dataKey] || [];
  const override = overrides[role.key] || {};
  const discoveredName = entries.map((p) => p.name).filter(Boolean).join(", ");
  const currentName = override.name || discoveredName;
  const currentNat = override.nationality || entries[0]?.nationality || "";
  const [nameDraft, setNameDraft] = useState(null); // null = not editing
  const [saving, setSaving] = useState(false);

  async function save(fields) {
    setSaving(true);
    try {
      await postPeople(fields);
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  function commitName() {
    const v = (nameDraft ?? "").trim();
    setNameDraft(null);
    if (v === currentName) return;
    save({ [`${role.key}_name`]: v || null });
  }

  return (
    <div className="pd-person">
      <div className="pd-row">
        <div className="pd-ident">
          <span className="pd-role">{role.label}</span>
          <input
            className={`pd-name-input ${!currentName ? "pd-missing" : ""}`}
            value={nameDraft ?? currentName}
            placeholder="Not yet named"
            disabled={saving}
            onFocus={() => setNameDraft(currentName)}
            onChange={(e) => setNameDraft(e.target.value)}
            onBlur={commitName}
            onKeyDown={(e) => { if (e.key === "Enter") e.currentTarget.blur(); }}
          />
        </div>
        <NationalitySelect
          value={currentNat}
          saving={saving}
          missing={!currentNat}
          onChange={(code) => save({ [`${role.key}_nationality`]: code })}
        />
      </div>
    </div>
  );
}

// Major Location Requirements — the canonical controlled taxonomy of
// physical location environments that materially differentiate
// jurisdiction suitability. Script analysis SEEDS the categories
// (production.physical_requirements.location_categories, evidence in the
// tooltip); clicking a chip toggles a user-confirmed override, persisted
// to the canonical Production Record (POST /locations) — the backend
// invalidates its cached state so territory matching and recommendations
// recompute. Script extraction is never overwritten; overrides layer on
// top and can be cleared.
function MajorLocations({ categories, onSaved }) {
  const [saving, setSaving] = useState(false);
  const entries = Object.entries(categories || {})
    .sort(([, a], [, b]) => (b.effective ? 1 : 0) - (a.effective ? 1 : 0));

  async function toggle(slug, cat) {
    setSaving(true);
    try {
      await postLocations({ [slug]: !cat.effective });
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="pd-locations">
      <div className="pd-section-label">Major location requirements</div>
      <p className="pd-req-note">Seeded from script analysis · click to confirm or override · drives jurisdiction matching</p>
      {entries.length === 0 ? (
        <p className="pd-loc-empty">No script analysis available yet.</p>
      ) : (
        <div className="tag-row">
          {entries.map(([slug, cat]) => (
            <button
              key={slug}
              className={`tag ${cat.effective ? "active" : ""} ${cat.override !== null && cat.override !== undefined ? "pd-overridden" : ""}`}
              disabled={saving}
              title={`${cat.evidence}${cat.source === "user_override" ? " — user override" : " — script analysis"}`}
              onClick={() => toggle(slug, cat)}
            >
              {cat.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProductionDetails({ people, requirements, refetch }) {
  const overrides = people?.overrides || {};
  return (
    <section className="pd-panel">
      <div className="pd-header">
        <span className="pd-title">Production facts</span>
        <span className="pd-col-label">Nationality</span>
      </div>

      {PERSON_ROLES.map((role) => (
        <FactRow key={role.key} role={role} people={people} overrides={overrides} onSaved={refetch} />
      ))}

      <MajorLocations categories={requirements?.location_categories} onSaved={refetch} />
    </section>
  );
}
