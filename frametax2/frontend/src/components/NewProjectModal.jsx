import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import {
  createProject, getOrganizations, discoverIngestion, updateIngestionCandidate, commitIngestionCandidate,
} from "../api";
import { PROJECT_STATUSES } from "../lib/useProjectStatus";
import IngestionSourceChooser from "./IngestionSourceChooser";

// "+ New Project" — reuses the existing Import Material source chooser
// and ingestion pipeline (discover/classify/dedup/commit) so a project
// can be created FROM its own real material in one flow, instead of
// create-empty -> leave -> Import Material -> re-associate. "Create
// Empty Project" keeps the original title-only form for the case where
// there's genuinely nothing to import yet. Every path still creates
// exactly one real Project via the same POST /api/v1/projects; material
// creation never invents a Document — it stages via discoverIngestion
// exactly like Import Material does, then commits only what's
// confidently classified, leaving the rest for review on the new
// Project's own Record.
const FORMATS = ["feature", "series", "documentary", "short"];

function guessTitleFromPath(path) {
  const base = (path.split("/").filter(Boolean).pop() || "").trim();
  if (!base) return "";
  const spaced = /[a-z][A-Z]/.test(base) && !base.includes(" ")
    ? base.replace(/([a-z])([A-Z])/g, "$1 $2") // camelCase -> spaced
    : base.replace(/[_-]+/g, " "); // snake_case / kebab-case -> spaced
  // Only re-case words that are all-lowercase or all-uppercase (i.e. not
  // already a deliberate mixed-case title like "McCarthy") — Title Case them.
  const titled = spaced.replace(/\S+/g, (word) => (
    /^[a-z]+$/.test(word) || /^[A-Z]+$/.test(word)
      ? word[0].toUpperCase() + word.slice(1).toLowerCase()
      : word
  ));
  return titled.replace(/\s+/g, " ").trim();
}

export default function NewProjectModal({ onClose, onCreated }) {
  const [step, setStep] = useState("choose"); // choose | empty | material
  const [source, setSource] = useState(null); // folder | files
  const [org, setOrg] = useState(null);
  const [orgError, setOrgError] = useState(null);

  // Empty-project form state (unchanged from the original modal).
  const [title, setTitle] = useState("");
  const [format, setFormat] = useState("");
  const [lifecycle, setLifecycle] = useState("evaluation");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Material-based creation state.
  const [path, setPath] = useState("");
  const [discovering, setDiscovering] = useState(false);
  const [candidates, setCandidates] = useState(null); // this discovery batch only, not the whole backlog
  const [materialTitle, setMaterialTitle] = useState("");
  const [creatingFromMaterial, setCreatingFromMaterial] = useState(false);
  const [createdProject, setCreatedProject] = useState(null);
  const [materialError, setMaterialError] = useState(null);

  useEffect(() => {
    getOrganizations()
      .then((orgs) => setOrg(orgs[0] || null))
      .catch((err) => setOrgError(err.message || String(err)));
  }, []);

  useEffect(() => {
    function onKey(e) { if (e.key === "Escape") onClose(); }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function submitEmpty(e) {
    e.preventDefault();
    if (!title.trim() || !org) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const project = await createProject({
        organization_id: org.id,
        title: title.trim(),
        format: format || null,
        lifecycle: lifecycle.toUpperCase(),
      });
      onCreated(project);
    } catch (err) {
      setSubmitError(err.message || String(err));
      setSubmitting(false);
    }
  }

  async function runDiscover(e) {
    e.preventDefault();
    if (!path.trim()) return;
    setDiscovering(true);
    setMaterialError(null);
    try {
      // No project_id yet — this project doesn't exist. Every candidate
      // comes back association_confidence "none"/"low" until the user
      // confirms the title below and we associate them explicitly.
      const result = await discoverIngestion(path.trim(), null);
      setCandidates(result.candidates);
      if (!materialTitle) setMaterialTitle(guessTitleFromPath(path.trim()));
    } catch (err) {
      setMaterialError(err.message || String(err));
    } finally {
      setDiscovering(false);
    }
  }

  async function createFromMaterial() {
    if (!materialTitle.trim() || !org) return;
    setCreatingFromMaterial(true);
    setMaterialError(null);
    try {
      const project = await createProject({
        organization_id: org.id, title: materialTitle.trim(), format: null, lifecycle: "EVALUATION",
      });
      // Associate every candidate from this discovery batch with the new
      // Project — the same PATCH the review-table "Project" dropdown
      // uses, which is also what promotes association_confidence to
      // "high" (a human just confirmed it). Then commit only the ones
      // whose CATEGORY is also confidently classified; anything else
      // stays staged for review on the new Project's own Record, same
      // as Import Material leaves it.
      const updated = [];
      for (const c of candidates || []) {
        const u = await updateIngestionCandidate(c.id, { proposed_project_id: project.id });
        updated.push(u);
      }
      const results = [];
      for (const c of updated) {
        if (c.category_confidence === "high") {
          const r = await commitIngestionCandidate(c.id);
          results.push({ ...c, committed: true, result: r.result });
        } else {
          results.push({ ...c, committed: false });
        }
      }
      setCandidates(results);
      setCreatedProject(project);
    } catch (err) {
      setMaterialError(err.message || String(err));
    } finally {
      setCreatingFromMaterial(false);
    }
  }

  const committedCount = (candidates || []).filter((c) => c.committed).length;
  const stagedCount = (candidates || []).length - committedCount;

  return createPortal(
    <div className="np-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={`np-modal ${step === "material" ? "np-modal-wide" : ""}`}>
        <div className="np-head">
          <h2>New Project</h2>
          <button type="button" className="np-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {orgError && <p className="np-error">Could not load organization: {orgError}</p>}

        {step === "choose" && (
          <>
            <p className="text-tertiary small ing-hint">How would you like to start?</p>
            <IngestionSourceChooser
              heading={null}
              extraOptions={[{ key: "empty", label: "Create Empty Project", desc: "Start with only project information — title, format, lifecycle." }]}
              onSelect={(key) => {
                if (key === "empty") setStep("empty");
                else if (key === "drive") { /* disabled option — no-op */ }
                else { setSource(key); setStep("material"); }
              }}
            />
          </>
        )}

        {step === "empty" && (
          <form onSubmit={submitEmpty}>
            <button type="button" className="ing-source-back" onClick={() => setStep("choose")}>← How would you like to start?</button>
            {submitError && <p className="np-error">{submitError}</p>}
            <label className="np-field">
              <span>Title</span>
              <input
                className="field-input" type="text" value={title}
                onChange={(e) => setTitle(e.target.value)} placeholder="Project title" autoFocus required
              />
            </label>
            <label className="np-field">
              <span>Format</span>
              <select className="field-input" value={format} onChange={(e) => setFormat(e.target.value)}>
                <option value="">Unspecified</option>
                {FORMATS.map((f) => <option key={f} value={f}>{f[0].toUpperCase() + f.slice(1)}</option>)}
              </select>
            </label>
            <label className="np-field">
              <span>Lifecycle</span>
              <select className="field-input" value={lifecycle} onChange={(e) => setLifecycle(e.target.value)}>
                {PROJECT_STATUSES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
              </select>
            </label>
            <div className="np-actions">
              <button type="button" className="hero-action" onClick={onClose}>Cancel</button>
              <button type="submit" className="hero-action primary" disabled={!title.trim() || !org || submitting}>
                {submitting ? "Creating…" : "Create Project"}
              </button>
            </div>
          </form>
        )}

        {step === "material" && (
          <div>
            <button type="button" className="ing-source-back" onClick={() => setStep("choose")}>← How would you like to start?</button>
            <p className="text-tertiary small ing-hint" style={{ marginTop: 6 }}>
              {source === "folder" ? "Point at a folder on this Mac." : "Enter the folder containing the specific file(s)."}
            </p>

            {materialError && <p className="np-error">{materialError}</p>}

            {!createdProject && (
              <form className="ing-discover-row" onSubmit={runDiscover}>
                <input
                  className="field-input" type="text" placeholder="Absolute folder path on this Mac…"
                  value={path} onChange={(e) => setPath(e.target.value)} autoFocus
                />
                <button className="hero-action primary" type="submit" disabled={discovering || !path.trim()}>
                  {discovering ? "Scanning…" : "Discover"}
                </button>
              </form>
            )}

            {candidates !== null && !createdProject && (
              <>
                <p className="text-tertiary small" style={{ marginTop: 10 }}>
                  {candidates.length === 0
                    ? "No files found at that path."
                    : `${candidates.length} file(s) found. Nothing is committed until you confirm the project below.`}
                </p>
                <label className="np-field">
                  <span>Project title</span>
                  <input
                    className="field-input" type="text" value={materialTitle}
                    onChange={(e) => setMaterialTitle(e.target.value)} placeholder="Project title"
                  />
                </label>
                <div className="np-actions">
                  <button type="button" className="hero-action" onClick={onClose}>Cancel</button>
                  <button
                    type="button" className="hero-action primary"
                    disabled={!materialTitle.trim() || !org || creatingFromMaterial}
                    onClick={createFromMaterial}
                  >
                    {creatingFromMaterial ? "Creating…" : "Create Project & Continue"}
                  </button>
                </div>
              </>
            )}

            {createdProject && (
              <>
                <p className="text-tertiary small" style={{ marginTop: 10 }}>
                  <strong>{createdProject.title}</strong> created — {committedCount} file(s) committed
                  {stagedCount > 0 ? `, ${stagedCount} left staged for review on its Record` : ""}.
                </p>
                {candidates.length > 0 && (
                  <div className="ing-table-wrap" style={{ marginTop: 8 }}>
                    <table className="ing-table">
                      <thead><tr><th>File</th><th>Category</th><th>Status</th></tr></thead>
                      <tbody>
                        {candidates.map((c) => (
                          <tr key={c.id}>
                            <td className="ing-fname">{c.filename}</td>
                            <td>{c.proposed_category}</td>
                            <td>{c.committed ? "Committed" : "Staged for review"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                <div className="np-actions">
                  <button type="button" className="hero-action primary" onClick={() => onCreated(createdProject)}>
                    Open Project Record →
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
}
