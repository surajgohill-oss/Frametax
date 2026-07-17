import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { postPeople } from "../api";

// Production Details panel — approved Overview left column.
// People rows use the REAL backend contract (POST /people, role-level
// nationality overrides — the backend's own model). Residency is not a
// permanent field here per the approved design; the backend override is
// left untouched when only nationality changes.
//
// The nationality dropdown offers common ISO2 values with demonym labels;
// any already-stored code outside this list is preserved as an option so
// an existing backend value is never clobbered by the UI.
const ROLES = [
  { key: "director", label: "Director", dataKey: "directors" },
  { key: "writer", label: "Writer", dataKey: "writers" },
  { key: "producer", label: "Producers", dataKey: "producers" },
  { key: "lead_cast", label: "Lead Cast", dataKey: "cast" },
];

const NATIONALITIES = [
  ["GB", "British"], ["US", "American"], ["FR", "French"], ["DE", "German"],
  ["IT", "Italian"], ["ES", "Spanish"], ["IE", "Irish"], ["MT", "Maltese"],
  ["MU", "Mauritian"], ["FJ", "Fijian"], ["AU", "Australian"], ["NZ", "New Zealander"],
  ["CA", "Canadian"], ["IN", "Indian"], ["ZA", "South African"],
];

function NationalitySelect({ value, onChange, disabled, saving }) {
  const known = NATIONALITIES.some(([code]) => code === value);
  return (
    <select
      className="pd-select"
      value={value || ""}
      disabled={disabled || saving}
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

function PersonRow({ role, people, overrides, onSaved }) {
  const entries = people[role.dataKey] || [];
  const override = overrides[role.key] || {};
  const current = override.nationality || entries[0]?.nationality || "";
  const [saving, setSaving] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const primary = entries[0];
  const extras = entries.slice(1);

  async function save(code) {
    setSaving(true);
    try {
      await postPeople({ [`${role.key}_nationality`]: code });
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="pd-person">
      <div className="pd-row">
        <div className="pd-ident">
          <span className="pd-role">{role.label}</span>
          <span className="pd-name">
            {primary?.name || <span className="text-tertiary">Not yet named</span>}
            {extras.length > 0 && (
              <button className="pd-expand" onClick={() => setExpanded((e) => !e)}>
                {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />} +{extras.length}
              </button>
            )}
          </span>
        </div>
        <NationalitySelect value={current} onChange={save} saving={saving} />
      </div>
      {expanded && extras.map((p) => (
        // Role-level nationality is the backend's own model — extra people
        // share the role's dropdown above rather than getting a second one.
        <div className="pd-row pd-row-extra" key={p.name}>
          <div className="pd-ident"><span className="pd-name">{p.name}</span></div>
          <span className="pd-extra-note text-tertiary small">same role override</span>
        </div>
      ))}
    </div>
  );
}

// Overview locations: production requirements, not jurisdiction candidates.
// Story Locations derive from the real script attributes; the other three
// categories have no backend source yet, so they render honest empty
// states (presentation-only — no fabricated fixture entries).
function LocationsAccordion({ script }) {
  const [open, setOpen] = useState({ story: true });
  const setting = script?.attributes?.setting?.value;
  const countries = script?.attributes?.countries?.value;
  const storyItems = [
    ...(setting ? String(setting).split(/[,;·]/).map((s) => s.trim()).filter(Boolean) : []),
    ...(countries ? [`Countries referenced — ${countries}`] : []),
  ];

  const groups = [
    { key: "story", label: "Story Locations", items: storyItems },
    { key: "environments", label: "Production Environments", items: [] },
    { key: "components", label: "Production Components", items: [] },
    { key: "locked", label: "Required / Locked Locations", items: [] },
  ];

  return (
    <div className="pd-locations">
      <div className="pd-section-label">Locations</div>
      {groups.map((g) => {
        const isOpen = !!open[g.key];
        return (
          <div className="pd-loc-group" key={g.key}>
            <button className="pd-loc-header" onClick={() => setOpen((o) => ({ ...o, [g.key]: !isOpen }))}>
              {isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
              <span>{g.label}</span>
              <span className="pd-loc-count">{g.items.length}</span>
            </button>
            {isOpen && (
              g.items.length > 0 ? (
                <ul className="pd-loc-items">
                  {g.items.map((item) => <li key={item}>{item}</li>)}
                </ul>
              ) : (
                <p className="pd-loc-empty">None recorded yet.</p>
              )
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function ProductionDetails({ people, script, refetch }) {
  const overrides = people?.overrides || {};
  const language = script?.attributes?.language?.value || "English";

  return (
    <section className="pd-panel">
      <div className="pd-header">
        <span className="pd-title">Production details</span>
        <span className="pd-col-label">Nationality</span>
      </div>

      {ROLES.map((role) => (
        <PersonRow key={role.key} role={role} people={people} overrides={overrides} onSaved={refetch} />
      ))}

      <div className="pd-person">
        <div className="pd-row">
          <div className="pd-ident">
            <span className="pd-role">Production Company</span>
            <span className="pd-name text-tertiary">Not tracked by this backend yet</span>
          </div>
          {/* Column heading is contextually COUNTRY for a company —
              disabled until a backend field exists. */}
          <select className="pd-select" disabled title="No backend field yet"><option>—</option></select>
        </div>
      </div>

      <div className="pd-person">
        <div className="pd-row">
          <div className="pd-ident">
            <span className="pd-role">Language</span>
            <span className="pd-name">Primary production language</span>
          </div>
          {/* Read-only: value comes from the parsed script (default English
              for new productions); no backend write path exists, so the
              control never overwrites a persisted value. */}
          <select className="pd-select" value={language} disabled title="From the parsed script — presentation-only">
            <option value={language}>{language}</option>
          </select>
        </div>
      </div>

      <LocationsAccordion script={script} />
    </section>
  );
}
