import { useState } from "react";
import { Pencil } from "lucide-react";
import { postPeople, postLocations } from "../api";
import { PERSON_ROLES } from "../lib/personRoles";

// Production Facts — approved Overview left column. READ-ONLY by default:
// one Edit control switches the entire panel into edit mode (names,
// nationalities, and major-location categories become editable together),
// with explicit Save / Cancel. Save batches only the CHANGED fields to
// the canonical Production Record (POST /people, POST /locations) and
// refetches, so the Question Engine / optimizer / Workspace Inputs /
// jurisdiction snapshots all recompute from the same record; Cancel
// discards the draft without touching anything. No permanent inline edit
// controls. Both surfaces (this panel and Workspace Inputs) render from
// the shared PERSON_ROLES schema — one record, one role vocabulary.
// Residency is deliberately absent here per the approved design.

const NATIONALITIES = [
  ["GB", "British"], ["US", "American"], ["FR", "French"], ["DE", "German"],
  ["IT", "Italian"], ["ES", "Spanish"], ["IE", "Irish"], ["MT", "Maltese"],
  ["MU", "Mauritian"], ["FJ", "Fijian"], ["AU", "Australian"], ["NZ", "New Zealander"],
  ["CA", "Canadian"], ["IN", "Indian"], ["ZA", "South African"],
];
const natLabel = (code) => (NATIONALITIES.find(([c]) => c === code) || [])[1] || code || "—";

function NationalitySelect({ value, onChange, disabled }) {
  const known = NATIONALITIES.some(([code]) => code === value);
  return (
    <select
      className={`pd-select ${!value ? "pd-missing" : ""}`}
      value={value || ""}
      disabled={disabled}
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

export default function ProductionDetails({ people, requirements, refetch }) {
  const overrides = people?.overrides || {};
  const categories = requirements?.location_categories || {};
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(null);
  const [saving, setSaving] = useState(false);

  // Effective current value per role — override (user-confirmed) over the
  // discovered/served person data. Same resolution the backend applies.
  const currentOf = (role) => {
    const entries = people[role.dataKey] || [];
    const o = overrides[role.key] || {};
    return {
      name: o.name || entries.map((p) => p.name).filter(Boolean).join(", "),
      nationality: o.nationality || entries[0]?.nationality || "",
    };
  };

  function beginEdit() {
    const p = {};
    for (const role of PERSON_ROLES) p[role.key] = { ...currentOf(role) };
    const l = {};
    for (const [slug, cat] of Object.entries(categories)) l[slug] = cat.effective;
    setDraft({ people: p, locations: l });
    setEditing(true);
  }

  function cancelEdit() {
    setDraft(null);
    setEditing(false);
  }

  async function saveEdit() {
    setSaving(true);
    try {
      const answers = {};
      for (const role of PERSON_ROLES) {
        const before = currentOf(role);
        const after = draft.people[role.key];
        const name = (after.name || "").trim();
        if (name !== before.name) answers[`${role.key}_name`] = name || null;
        if ((after.nationality || "") !== before.nationality) {
          answers[`${role.key}_nationality`] = after.nationality || null;
        }
      }
      const locs = {};
      for (const [slug, cat] of Object.entries(categories)) {
        if (draft.locations[slug] !== cat.effective) locs[slug] = draft.locations[slug];
      }
      if (Object.keys(answers).length) await postPeople(answers);
      if (Object.keys(locs).length) await postLocations(locs);
      refetch();
      setEditing(false);
      setDraft(null);
    } finally {
      setSaving(false);
    }
  }

  const setPerson = (key, field, value) =>
    setDraft((d) => ({ ...d, people: { ...d.people, [key]: { ...d.people[key], [field]: value } } }));
  const toggleLocation = (slug) =>
    setDraft((d) => ({ ...d, locations: { ...d.locations, [slug]: !d.locations[slug] } }));

  const catEntries = Object.entries(categories)
    .sort(([, a], [, b]) => (b.effective ? 1 : 0) - (a.effective ? 1 : 0));

  return (
    <section className="pd-panel">
      <div className="pd-header">
        <span className="pd-title-row">
          <span className="pd-title">Production facts</span>
          {editing ? (
            <span className="pd-edit-actions">
              <button className="ghost-action small" onClick={saveEdit} disabled={saving}>{saving ? "Saving…" : "Save"}</button>
              <button className="ghost-action small" onClick={cancelEdit} disabled={saving}>Cancel</button>
            </span>
          ) : (
            <button className="pd-edit-btn" title="Edit production facts" aria-label="Edit production facts" onClick={beginEdit}>
              <Pencil size={13} />
            </button>
          )}
        </span>
        <span className="pd-col-label">Nationality</span>
      </div>

      {PERSON_ROLES.map((role) => {
        const cur = editing ? draft.people[role.key] : currentOf(role);
        return (
          <div className="pd-person" key={role.key}>
            <div className="pd-row">
              <div className="pd-ident">
                <span className="pd-role">{role.label}</span>
                {editing ? (
                  <input
                    className={`pd-name-input ${!cur.name ? "pd-missing" : ""}`}
                    value={cur.name}
                    placeholder="Not yet named"
                    disabled={saving}
                    onChange={(e) => setPerson(role.key, "name", e.target.value)}
                  />
                ) : (
                  <span className="pd-name">
                    {cur.name || <span className="text-tertiary">Not yet named</span>}
                  </span>
                )}
              </div>
              {editing ? (
                <NationalitySelect
                  value={cur.nationality}
                  disabled={saving}
                  onChange={(code) => setPerson(role.key, "nationality", code)}
                />
              ) : (
                <span className={`pd-nat-value ${!cur.nationality ? "pd-nat-missing" : ""}`}>
                  {natLabel(cur.nationality)}
                </span>
              )}
            </div>
          </div>
        );
      })}

      {/* Major Location Requirements — canonical taxonomy seeded from
          script analysis (evidence in tooltips); editable only within the
          panel's edit mode, persisted as overrides on Save. */}
      <div className="pd-locations">
        <div className="pd-section-label">Major location requirements</div>
        <p className="pd-req-note">
          Seeded from script analysis · drives jurisdiction matching
          {editing ? " · click to toggle" : ""}
        </p>
        {catEntries.length === 0 ? (
          <p className="pd-loc-empty">No script analysis available yet.</p>
        ) : (
          <div className="tag-row">
            {catEntries.map(([slug, cat]) => {
              const active = editing ? draft.locations[slug] : cat.effective;
              const overridden = cat.override !== null && cat.override !== undefined;
              return editing ? (
                <button
                  key={slug}
                  className={`tag ${active ? "active" : ""}`}
                  disabled={saving}
                  title={cat.evidence}
                  onClick={() => toggleLocation(slug)}
                >
                  {cat.label}
                </button>
              ) : (
                <span
                  key={slug}
                  className={`tag pd-tag-static ${active ? "active" : ""} ${overridden ? "pd-overridden" : ""}`}
                  title={`${cat.evidence}${cat.source === "user_override" ? " — user override" : " — script analysis"}`}
                >
                  {cat.label}
                </span>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
