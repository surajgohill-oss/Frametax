import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_ORIGIN, getProjects } from "../../api";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import { PROJECT_STATUSES } from "../../lib/useProjectStatus";
import { getTheme, toggleTheme } from "../../lib/theme";
import NewProjectModal from "../../components/NewProjectModal";
import IngestionReviewModal from "../../components/IngestionReviewModal";

// Project Library — CineGlobe's durable production corpus. Every real
// persisted Project (Phase C migrated the first one; this is where a
// second, third, and a historical corpus will eventually live), not a
// second Today dashboard: no NPC, no scenario economics, no jurisdiction
// comparison — those are optimizer output and belong on Overview/
// Workspace, not on a durable-corpus summary card.
//
// Reuses the existing Company page shell (.screen/.screen-header, the
// Today toolbar pattern, .tag filters, Money) — no new shell, no new
// button style, no new filter-chip treatment.

const MATERIAL_LABELS = [
  { key: "script", label: "Script" },
  { key: "budget", label: "Budget" },
  { key: "deck", label: "Deck" },
  { key: "schedule", label: "Schedule" },
];

const SORTS = [
  { key: "updated", label: "Recently Updated" },
  { key: "title", label: "Title" },
  { key: "budget", label: "Budget" },
];

function lifecycleMeta(lifecycle) {
  const key = (lifecycle || "evaluation").toLowerCase();
  return PROJECT_STATUSES.find((s) => s.key === key) || PROJECT_STATUSES[0];
}

export default function ProjectLibrary() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState("updated");
  const [newOpen, setNewOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  // Same canonical theme module Today.jsx uses — Company routes render no
  // ProjectHeader, so this is its own trigger for the SAME theme state
  // (document.documentElement's data-theme attribute), never a second
  // theme implementation.
  const [theme, setThemeState] = useState(getTheme);

  function load() {
    setError(null);
    getProjects().then(setProjects).catch((err) => setError(err.message || String(err)));
  }
  useEffect(() => { load(); }, []);

  const counts = useMemo(() => {
    const c = { all: projects?.length || 0 };
    for (const s of PROJECT_STATUSES) c[s.key] = 0;
    for (const p of projects || []) {
      const key = (p.lifecycle || "evaluation").toLowerCase();
      c[key] = (c[key] || 0) + 1;
    }
    return c;
  }, [projects]);

  const visible = useMemo(() => {
    let list = projects || [];
    if (filter !== "all") list = list.filter((p) => (p.lifecycle || "").toLowerCase() === filter);
    const q = query.trim().toLowerCase();
    if (q) list = list.filter((p) => p.title.toLowerCase().includes(q));
    const sorted = [...list];
    if (sort === "title") sorted.sort((a, b) => a.title.localeCompare(b.title));
    else if (sort === "budget") sorted.sort((a, b) => (b.total_budget_usd || 0) - (a.total_budget_usd || 0));
    else sorted.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
    return sorted;
  }, [projects, filter, query, sort]);

  if (error) return <div className="screen"><ErrorBox message={error} /></div>;
  if (!projects) return <div className="screen"><Loading /></div>;

  return (
    <div className="screen lib-screen">
      <div className="lib-head">
        <div>
          <p className="screen-eyebrow">Company</p>
          <h1 className="screen-title">Project Library</h1>
          <p className="lib-sub">All productions across the company</p>
        </div>
        <div className="lib-head-actions">
          <button
            className="ph-ico"
            title={theme === "night" ? "Switch to day mode" : "Switch to night mode"}
            aria-label={theme === "night" ? "Switch to day mode" : "Switch to night mode"}
            aria-pressed={theme === "night"}
            onClick={() => setThemeState(toggleTheme())}
          >
            {theme === "night" ? "☾" : "◐"}
          </button>
          <button className="hero-action" onClick={() => setImportOpen(true)}>Import Material</button>
          <button className="hero-action primary" onClick={() => setNewOpen(true)}>+ New Project</button>
        </div>
      </div>

      <div className="lib-searchrow">
        <input
          className="field-input lib-search"
          type="text"
          placeholder="Search projects by title or alias…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="lib-filterrow">
        <div className="tag-row lib-tags">
          <button className={`tag ${filter === "all" ? "active" : ""}`} onClick={() => setFilter("all")}>
            All <span className="lib-tag-n">{counts.all}</span>
          </button>
          {PROJECT_STATUSES.map((s) => (
            <button
              key={s.key}
              className={`tag ${filter === s.key ? "active" : ""}`}
              onClick={() => setFilter(s.key)}
            >
              {s.label} <span className="lib-tag-n">{counts[s.key] || 0}</span>
            </button>
          ))}
        </div>
        <select className="field-input lib-sort" value={sort} onChange={(e) => setSort(e.target.value)}>
          {SORTS.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
        </select>
      </div>

      {visible.length === 0 ? (
        <div className="empty-state">
          {projects.length === 0
            ? "No projects yet — create the first one to start the Library."
            : "No projects match this search or filter."}
        </div>
      ) : (
        <div className={`lib-grid ${filter === "all" ? "compact" : ""}`}>
          {visible.map((p) => {
            const meta = lifecycleMeta(p.lifecycle);
            return (
              <button
                key={p.id}
                className={`lib-card ${filter === "all" ? "compact" : ""} ${meta.key === "archived" ? "arch" : ""}`}
                onClick={() => navigate(`/company/library/${p.id}`)}
              >
                <div className="lib-art">
                  {p.artwork_url
                    ? <img src={`${API_ORIGIN}${p.artwork_url}`} alt="" />
                    : <span className="lib-noart">No artwork yet</span>}
                </div>
                <div className="lib-body">
                  <div className="lib-stage"><span className={`dot ${meta.tier}`} />{meta.label}</div>
                  <div className="lib-title">{p.title}</div>
                  <div className="lib-meta">
                    <span>{p.format ? p.format[0].toUpperCase() + p.format.slice(1) : "Format unknown"}</span>
                    <span className="lib-dot-sep">·</span>
                    {p.total_budget_usd != null ? <Money value={p.total_budget_usd} /> : <span className="text-tertiary">Budget unknown</span>}
                  </div>
                  <div className="lib-pips">
                    {MATERIAL_LABELS.map((m) => (
                      <span key={m.key} className={`lib-pip ${p.materials[m.key] ? "have" : ""}`}>{m.label}</span>
                    ))}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {newOpen && (
        <NewProjectModal
          onClose={() => setNewOpen(false)}
          onCreated={(project) => { setNewOpen(false); navigate(`/company/library/${project.id}`); }}
        />
      )}

      {importOpen && (
        <IngestionReviewModal
          onClose={() => setImportOpen(false)}
          onCommitted={() => { setImportOpen(false); load(); }}
        />
      )}
    </div>
  );
}
