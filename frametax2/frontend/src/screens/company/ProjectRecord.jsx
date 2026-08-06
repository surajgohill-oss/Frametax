import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { API_ORIGIN, deleteProject, getProjectRecord, setMasterArtwork } from "../../api";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import { PROJECT_STATUSES } from "../../lib/useProjectStatus";
import { getTheme, toggleTheme } from "../../lib/theme";
import IngestionReviewModal from "../../components/IngestionReviewModal";
import DeleteProjectDialog from "../../components/DeleteProjectDialog";

// Project Record — "what do we know and possess about this production?"
// Not a replacement for Overview/Workspace: no economics, no scenario
// comparison, no optimizer output beyond the two honest facts (has
// evaluation begun, how many structures exist, which one leads). Full
// page inside the existing shell — the Inspector drawer already owns
// production-scoped selection, and five substantial content groups
// (identity, materials, people, analysis, history) exceed what a drawer
// holds without becoming its own scrolling page.

const TABS = ["Overview", "Documents", "People", "Facts", "Locations", "Analysis", "History"];

const CATEGORY_LABELS = {
  screenplay: "Screenplay", budget: "Budget", schedule: "Schedule", deck: "Deck",
  lookbook: "Look Book", finance: "Finance Plan", cast: "Cast", crew: "Crew",
  incentive: "Incentive", legal: "Legal", artwork: "Artwork", other: "Other",
};

function lifecycleMeta(lifecycle) {
  const key = (lifecycle || "evaluation").toLowerCase();
  return PROJECT_STATUSES.find((s) => s.key === key) || PROJECT_STATUSES[0];
}

function fmtBytes(n) {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} MB`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)} KB`;
  return `${n} B`;
}

export default function ProjectRecord() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("Overview");
  const [theme, setThemeState] = useState(getTheme);
  const [importOpen, setImportOpen] = useState(false);
  const [artworkPickerOpen, setArtworkPickerOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  function load() {
    setError(null);
    getProjectRecord(projectId).then(setRecord).catch((err) => setError(err.message || String(err)));
  }

  useEffect(() => {
    setRecord(null);
    setTab("Overview");
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  if (error) return <div className="screen"><ErrorBox message={error} /></div>;
  if (!record) return <div className="screen"><Loading /></div>;

  const { project, organization, aliases, artwork, documents, people, facts, locations, analysis, activity } = record;
  const meta = lifecycleMeta(project.lifecycle);
  const isServedProduction = project.is_served_production;

  async function selectMaster(assetId) {
    await setMasterArtwork(project.id, assetId);
    setArtworkPickerOpen(false);
    load();
  }

  return (
    <div className="screen rec-screen">
      <div className="rec-toprow">
        <div className="rec-crumb" onClick={() => navigate("/company/library")}>← Project Library</div>
        <div className="rec-toprow-actions">
          <button
            className="ph-ico"
            title={theme === "night" ? "Switch to day mode" : "Switch to night mode"}
            aria-label={theme === "night" ? "Switch to day mode" : "Switch to night mode"}
            aria-pressed={theme === "night"}
            onClick={() => setThemeState(toggleTheme())}
          >
            {theme === "night" ? "☾" : "◐"}
          </button>
          <button className="hero-action" onClick={() => setImportOpen(true)}>Add Material</button>
        </div>
      </div>

      <div className="rec-idband">
        <div className="rec-idart">
          {artwork.master
            ? <img src={`${API_ORIGIN}${artwork.master.url}`} alt="" />
            : <span className="lib-noart">No artwork yet</span>}
          {artwork.candidates.length > 0 && (
            <button className="rec-art-change" onClick={() => setArtworkPickerOpen((v) => !v)}>Change Artwork ▾</button>
          )}
        </div>
        <div className="rec-idmain">
          <div className="rec-title">{project.title}</div>
          {aliases.length > 0 && <div className="rec-alias">Also known as {aliases.map((a) => `"${a}"`).join(", ")}</div>}
          <div className="rec-idrow">
            <div className="rec-idf">
              <span className="l2">Lifecycle</span>
              <span className="v"><span className={`dot ${meta.tier}`} /> {meta.label}</span>
            </div>
            <div className="rec-idf">
              <span className="l2">Format</span>
              <span className="v">{project.format ? project.format[0].toUpperCase() + project.format.slice(1) : "—"}</span>
            </div>
            <div className="rec-idf">
              <span className="l2">Budget</span>
              <span className="v">{project.total_budget_usd != null ? <Money value={project.total_budget_usd} /> : "—"}</span>
            </div>
            <div className="rec-idf">
              <span className="l2">Organization</span>
              <span className="v">{organization?.name || "—"}</span>
            </div>
            {project.target_shoot_year && (
              <div className="rec-idf"><span className="l2">Shoot year</span><span className="v mono">{project.target_shoot_year}</span></div>
            )}
          </div>
          {artworkPickerOpen && (
            <div className="rec-art-picker">
              {artwork.candidates.map((c) => (
                <button key={c.id} className={`rec-art-cand ${c.is_master ? "on" : ""}`} onClick={() => selectMaster(c.id)}>
                  <img src={`${API_ORIGIN}${c.url}`} alt="" />
                  {c.is_master && <span className="rec-art-master-tag">Master</span>}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="rec-idact">
          {isServedProduction ? (
            <button className="hero-action primary" onClick={() => navigate("/production/overview")}>
              Open Production →
            </button>
          ) : (
            <button className="hero-action primary" disabled title="Evaluation is not yet wired to arbitrary Library projects — Little Utopia only">
              Begin Evaluation
            </button>
          )}
          {!isServedProduction && (
            <button className="rec-delete-link" onClick={() => setDeleteOpen(true)}>Delete Project…</button>
          )}
        </div>
      </div>

      <div className="rec-tabs">
        {TABS.map((t) => (
          <button key={t} className={`rec-tab ${tab === t ? "on" : ""}`} onClick={() => setTab(t)}>{t}</button>
        ))}
      </div>

      {tab === "Overview" && (
        <div className="rec-cols">
          <div>
            <MaterialsPanel documents={documents} isServedProduction={isServedProduction} navigate={navigate} />
            <KnownInfoPanel people={people} locations={locations} onViewAll={() => setTab("People")} />
          </div>
          <div>
            <AnalysisPanel analysis={analysis} />
            <ActivityPanel activity={activity} onViewAll={() => setTab("History")} limit={5} />
          </div>
        </div>
      )}

      {tab === "Documents" && (
        <div className="ovx-sec">
          <div className="oh"><b>Materials</b><span className="n">{documents.length}</span></div>
          <DocumentRows documents={documents} full />
          {isServedProduction && (
            <p className="rec-note">
              Full document management (upload, extraction, evidence trace) lives in{" "}
              <button className="rec-inline-link" onClick={() => navigate("/production/binder")}>Documents →</button>
            </p>
          )}
        </div>
      )}

      {tab === "People" && (
        <div className="ovx-sec">
          <div className="oh"><b>Known production information</b></div>
          {people.length === 0 ? (
            <div className="empty-state">No people recorded yet.</div>
          ) : (
            people.map((p, i) => (
              <div className="prow" key={i}>
                <span className="k">{p.role}</span>
                <span className="v">
                  {p.name}
                  {p.nationality && <span className="nat"> · {p.nationality}</span>}
                  {p.residency && <span className="nat"> · resident {p.residency}</span>}
                </span>
              </div>
            ))
          )}
        </div>
      )}

      {tab === "Facts" && (
        <div className="ovx-sec">
          <div className="oh"><b>Persisted facts</b><span className="n">{facts.length}</span></div>
          {facts.length === 0 ? (
            <div className="empty-state">No facts recorded yet.</div>
          ) : (
            facts.map((f) => (
              <div className="stat" key={f.fact_key}>
                <span className="l">{f.fact_key.replace(/_/g, " ")}</span>
                <span className="v">{f.value ?? <span className="text-tertiary">unknown</span>}</span>
              </div>
            ))
          )}
        </div>
      )}

      {tab === "Locations" && (
        <div className="ovx-sec">
          <div className="oh"><b>Location requirements</b><span className="n">{locations.length}</span></div>
          {locations.length === 0 ? (
            <div className="empty-state">No location requirements recorded yet.</div>
          ) : (
            locations.map((l, i) => (
              <div className="prow" key={i}>
                <span className="k">{l.is_flexible === false ? "Fixed" : l.is_flexible === true ? "Flexible" : "—"}</span>
                <span className="v">{l.description}{l.notes && <div className="text-tertiary small">{l.notes}</div>}</span>
              </div>
            ))
          )}
        </div>
      )}

      {tab === "Analysis" && <AnalysisPanel analysis={analysis} full />}

      {tab === "History" && <ActivityPanel activity={activity} full />}

      {importOpen && (
        <IngestionReviewModal
          scopeProjectId={project.id}
          onClose={() => setImportOpen(false)}
          onCommitted={() => { setImportOpen(false); load(); }}
        />
      )}

      {deleteOpen && (
        <DeleteProjectDialog
          project={project}
          onClose={() => setDeleteOpen(false)}
          onDeleted={() => navigate("/company/library")}
        />
      )}
    </div>
  );
}

function DocumentRows({ documents, full }) {
  const core = ["screenplay", "budget", "deck", "schedule"];
  const rows = full ? documents : documents.filter((d) => core.includes(d.category));
  const missingCore = core.filter((c) => !documents.some((d) => d.category === c));
  return (
    <>
      {rows.map((d) => (
        <div className="mrow" key={d.category + d.title}>
          <span className="k">{CATEGORY_LABELS[d.category] || d.category}</span>
          <span className="f">{d.current_version?.filename || "—"}</span>
          <span className="v">
            {d.current_version?.version_label || (d.version_count > 1 ? `${d.version_count} versions` : "")}
            {" · "}{fmtBytes(d.current_version?.file_size)}
          </span>
          {d.current_unresolved && <span className="rec-conflict">{d.version_count} versions · CURRENT UNRESOLVED</span>}
          {d.current_version?.file_url
            ? <a className="lk" href={`${API_ORIGIN}${d.current_version.file_url}`} target="_blank" rel="noreferrer">View →</a>
            : <span className="lk" style={{ visibility: "hidden" }}>View →</span>}
        </div>
      ))}
      {full && missingCore.map((c) => (
        <div className="mrow" key={c}>
          <span className="k">{CATEGORY_LABELS[c]}</span>
          <span className="f miss">Not held</span>
          <span className="v"></span>
        </div>
      ))}
    </>
  );
}

function MaterialsPanel({ documents, isServedProduction, navigate }) {
  return (
    <div className="ovx-sec">
      <div className="oh"><b>Materials</b><span className="n">{documents.length}</span>
        {isServedProduction && <span className="act" onClick={() => navigate("/production/binder")}>Documents →</span>}
      </div>
      <DocumentRows documents={documents} full />
    </div>
  );
}

function KnownInfoPanel({ people, locations, onViewAll }) {
  const byRole = {};
  for (const p of people) (byRole[p.role] ||= []).push(p);
  const rows = [
    { label: "Writer", people: byRole.writer },
    { label: "Director", people: byRole.director },
    { label: "Producers", people: byRole.producer },
  ];
  return (
    <div className="ovx-sec">
      <div className="oh"><b>Known production information</b><span className="act" onClick={onViewAll}>View all →</span></div>
      {rows.map((r) => (
        <div className="prow" key={r.label}>
          <span className="k">{r.label}</span>
          <span className="v">
            {r.people && r.people.length
              ? r.people.map((p) => p.name).join(", ")
              : <span className="unk">Not yet known</span>}
          </span>
        </div>
      ))}
      <div className="prow">
        <span className="k">Locations</span>
        <span className="v">
          {locations.length ? (
            <div className="chips">
              {locations.slice(0, 6).map((l, i) => <span className="chip on" key={i}>{l.description}</span>)}
            </div>
          ) : <span className="unk">None recorded</span>}
        </span>
      </div>
    </div>
  );
}

function AnalysisPanel({ analysis, full }) {
  return (
    <div className="ovx-sec">
      <div className="oh"><b>Analysis</b></div>
      <div className="stat"><span className="l">Evaluation</span>
        <span className="v" style={{ color: analysis.evaluation_begun ? "var(--jade)" : undefined }}>
          {analysis.evaluation_begun ? "In progress" : "Not begun"}
        </span>
      </div>
      <div className="stat"><span className="l">Structures generated</span><span className="v mono">{analysis.structures_available}</span></div>
      <div className="stat"><span className="l">Leading structure</span>
        <span className="v">{analysis.leading_structure_name || <span className="text-tertiary">None yet</span>}</span>
      </div>
      {full && (
        <p className="text-tertiary small" style={{ marginTop: 10 }}>
          Structure count and leading structure are read directly from persisted Project Library state — never
          computed here, and reading this panel never triggers the optimizer.
        </p>
      )}
    </div>
  );
}

function ActivityPanel({ activity, onViewAll, limit, full }) {
  const rows = limit ? activity.slice(0, limit) : activity;
  return (
    <div className="ovx-sec">
      <div className="oh"><b>{full ? "Full history" : "Activity"}</b>{onViewAll && <span className="act" onClick={onViewAll}>View all →</span>}</div>
      {rows.length === 0 ? (
        <div className="empty-state">No activity recorded yet.</div>
      ) : (
        rows.map((a, i) => (
          <div className="arow" key={i}>
            <span className="d mono">{new Date(a.created_at).toLocaleDateString()}</span>
            <span className="t">{a.action} · {a.entity_type}{a.actor ? ` · ${a.actor}` : ""}</span>
          </div>
        ))
      )}
    </div>
  );
}
