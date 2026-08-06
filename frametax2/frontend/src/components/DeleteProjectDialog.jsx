import { useState } from "react";
import { createPortal } from "react-dom";
import { deleteProject } from "../api";

// Permanent deletion — the opposite of Archive. Archive keeps a project
// and its history intact; this removes the CineGlobe record and every
// record it owns entirely, for the accidental/test/duplicate case.
// Requires the title typed back, exactly, before the destructive button
// is even enabled — a project this consequential doesn't get a single
// careless click.
export default function DeleteProjectDialog({ project, onClose, onDeleted }) {
  const [confirmText, setConfirmText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const canDelete = confirmText.trim() === project.title;

  async function confirmDelete() {
    setBusy(true);
    setError(null);
    try {
      await deleteProject(project.id);
      onDeleted();
    } catch (err) {
      setError(err.message || String(err));
      setBusy(false);
    }
  }

  return createPortal(
    <div className="np-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget && !busy) onClose(); }}>
      <div className="np-modal del-modal">
        <div className="np-head">
          <h2>Delete Project</h2>
          <button type="button" className="np-close" onClick={onClose} disabled={busy} aria-label="Close">✕</button>
        </div>

        <p className="del-warning">
          This permanently removes <b>{project.title}</b> from CineGlobe — its documents, versions, artwork,
          facts, people, location requirements, and structures. This cannot be undone.
        </p>
        <p className="text-tertiary small">
          Original files on Drive or this Mac are never touched — only CineGlobe's own record of this project.
        </p>

        {error && <p className="np-error">{error}</p>}

        <label className="np-field">
          <span>Type the project title to confirm: {project.title}</span>
          <input
            className="field-input"
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder={project.title}
            autoFocus
          />
        </label>

        <div className="np-actions">
          <button type="button" className="hero-action" onClick={onClose} disabled={busy}>Cancel</button>
          <button type="button" className="hero-action destructive" onClick={confirmDelete} disabled={!canDelete || busy}>
            {busy ? "Deleting…" : "Delete Project"}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
