import { useState } from "react";
import { postPeople, postFacts } from "../api";

// Every editable control here maps to a REAL backend mutation
// (POST /people, POST /facts) — confirmed against app/api/v1/cineglobe.py
// and app/demo/little_utopia_state.py before writing this. Overrides are
// ROLE-level (one value per writer/director/lead_cast/producer), not
// per-person — that is the backend's own model, not a UI simplification.
// Fields the user requested that have NO backend-editable field yet
// (Department heads, Production companies, full Cast beyond lead, a
// Shoot-locations field distinct from the script's own "setting") are
// shown read-only or disclosed as unavailable — never fabricated.

const ROLES = [
  { key: "writer", label: "Writer", dataKey: "writers" },
  { key: "director", label: "Director", dataKey: "directors" },
  { key: "lead_cast", label: "Lead Cast", dataKey: "cast" },
  { key: "producer", label: "Producer(s)", dataKey: "producers" },
];

function Iso2Input({ value, onChange }) {
  return (
    <input
      className="field-input"
      style={{ width: 44, textAlign: "center" }}
      maxLength={2}
      placeholder="—"
      value={value}
      onChange={(e) => onChange(e.target.value.toUpperCase().replace(/[^A-Z]/g, ""))}
    />
  );
}

export function PeopleRow({ role, people, overrides, onSaved }) {
  const entries = people[role.dataKey] || [];
  const override = overrides[role.key] || { nationality: null, residency: null };
  const [nat, setNat] = useState(override.nationality || "");
  const [res, setRes] = useState(override.residency || "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const currentNat = override.nationality || entries[0]?.nationality || "—";
  const currentRes = override.residency || entries[0]?.residency || "—";

  async function save() {
    setSaving(true);
    setSaved(false);
    try {
      await postPeople({
        [`${role.key}_nationality`]: nat || null,
        [`${role.key}_residency`]: res || null,
      });
      setSaved(true);
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="field-row">
      <span className="field-label">
        {role.label}
        {entries.length > 0 && (
          <span className="text-tertiary small"> — {entries.map((p) => p.name).join(", ")}</span>
        )}
      </span>
      <div className="field-control">
        <span className="text-tertiary small mono">now {currentNat}/{currentRes}</span>
        <Iso2Input value={nat} onChange={setNat} />
        <Iso2Input value={res} onChange={setRes} />
        <button className="ghost-action small" onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save"}
        </button>
        {saved && <span className="field-saved">Saved</span>}
      </div>
    </div>
  );
}

function BoolFactRow({ factKey, meta, current, onSaved }) {
  const [saving, setSaving] = useState(false);
  async function set(value) {
    setSaving(true);
    try {
      await postFacts({ [factKey]: value });
      onSaved();
    } finally {
      setSaving(false);
    }
  }
  return (
    <div className="field-row">
      <span className="field-label" title={meta.description}>{factKey.replace(/_/g, " ")}</span>
      <div className="field-control">
        <span className="text-tertiary small">now {current === null ? "unset" : String(current)}</span>
        <button className={`tag ${current === true ? "active" : ""}`} disabled={saving} onClick={() => set(true)}>True</button>
        <button className={`tag ${current === false ? "active" : ""}`} disabled={saving} onClick={() => set(false)}>False</button>
      </div>
    </div>
  );
}

export function StrFactRow({ factKey, meta, current, onSaved, label }) {
  const [value, setValue] = useState(current || "");
  const [saving, setSaving] = useState(false);
  async function save() {
    setSaving(true);
    try {
      await postFacts({ [factKey]: value || null });
      onSaved();
    } finally {
      setSaving(false);
    }
  }
  return (
    <div className="field-row">
      <span className="field-label" title={meta.description}>{label || factKey.replace(/_/g, " ")}</span>
      <div className="field-control">
        <span className="text-tertiary small mono">now {current || "unset"}</span>
        <input
          className="field-input"
          style={{ width: 64 }}
          value={value}
          onChange={(e) => setValue(e.target.value.toUpperCase())}
          placeholder="ISO2"
        />
        <button className="ghost-action small" onClick={save} disabled={saving}>{saving ? "Saving…" : "Save"}</button>
      </div>
    </div>
  );
}

export default function QualificationPanel({ people, facts, script, refetch }) {
  const answerable = facts.answerable || {};
  const answers = facts.answers || {};

  return (
    <section className="region">
      <div className="region-title"><span>Qualification</span></div>
      <p className="text-tertiary small" style={{ marginBottom: 10 }}>
        Populated from the real production package. Every edit here re-derives qualification, treaty, and
        allocation results on the backend immediately — nothing is computed client-side.
      </p>

      <p className="field-label" style={{ marginBottom: 4, fontWeight: 500 }}>People — nationality / residency</p>
      <div className="row-list" style={{ marginBottom: 14 }}>
        {ROLES.map((role) => (
          <PeopleRow key={role.key} role={role} people={people} overrides={people.overrides || {}} onSaved={refetch} />
        ))}
      </div>

      <p className="field-label" style={{ marginBottom: 4, fontWeight: 500 }}>Production facts</p>
      <div className="row-list" style={{ marginBottom: 14 }}>
        {Object.entries(answerable).map(([key, meta]) =>
          meta.type === "bool" ? (
            <BoolFactRow key={key} factKey={key} meta={meta} current={answers[key] ?? null} onSaved={refetch} />
          ) : (
            <StrFactRow key={key} factKey={key} meta={meta} current={answers[key] ?? null} onSaved={refetch} />
          )
        )}
      </div>

      <p className="field-label" style={{ marginBottom: 4, fontWeight: 500 }}>Script &amp; locations (read-only)</p>
      <div className="row-list">
        <div className="field-row">
          <span className="field-label">Language</span>
          <span className="text-secondary small">{script.attributes?.language?.value || "unknown"}</span>
        </div>
        <div className="field-row">
          <span className="field-label">Script locations (setting)</span>
          <span className="text-secondary small">{script.attributes?.setting?.value || "unknown"}</span>
        </div>
        <div className="field-row">
          <span className="field-label">Countries referenced</span>
          <span className="text-secondary small">{script.attributes?.countries?.value || "unknown"}</span>
        </div>
        <div className="field-row">
          <span className="field-label field-unavailable">Department heads</span>
          <span className="field-unavailable">not tracked by this backend yet</span>
        </div>
        <div className="field-row">
          <span className="field-label field-unavailable">Production companies</span>
          <span className="field-unavailable">not tracked by this backend yet</span>
        </div>
      </div>
    </section>
  );
}
