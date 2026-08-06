import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { createProject, getOrganizations } from "../api";
import { PROJECT_STATUSES } from "../lib/useProjectStatus";

// Compact "+ New Project" modal — Title required, Format/Lifecycle
// optional (lifecycle defaults Evaluation). Creates exactly one real
// Project row via the existing POST /api/v1/projects. No optimizer run,
// no document scan — a title-only record is a legitimate, honestly-
// incomplete Library entry, not a placeholder to be filled in later by
// this dialog.
const FORMATS = ["feature", "series", "documentary", "short"];

export default function NewProjectModal({ onClose, onCreated }) {
  const [org, setOrg] = useState(null);
  const [orgError, setOrgError] = useState(null);
  const [title, setTitle] = useState("");
  const [format, setFormat] = useState("");
  const [lifecycle, setLifecycle] = useState("evaluation");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

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

  async function submit(e) {
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

  return createPortal(
    <div className="np-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <form className="np-modal" onSubmit={submit}>
        <div className="np-head">
          <h2>New Project</h2>
          <button type="button" className="np-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {orgError && <p className="np-error">Could not load organization: {orgError}</p>}
        {submitError && <p className="np-error">{submitError}</p>}

        <label className="np-field">
          <span>Title</span>
          <input
            className="field-input"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Project title"
            autoFocus
            required
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
    </div>,
    document.body,
  );
}
