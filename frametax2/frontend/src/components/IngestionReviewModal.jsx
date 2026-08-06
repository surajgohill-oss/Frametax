import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import {
  discoverIngestion, listIngestionCandidates, updateIngestionCandidate,
  commitIngestionCandidate, ignoreIngestionCandidate, getProjects,
} from "../api";
import IngestionSourceChooser, { INGESTION_SOURCES } from "./IngestionSourceChooser";

// Phase E — DISCOVER -> CLASSIFY -> ASSOCIATE -> STAGE -> REVIEW -> COMMIT,
// the shared review workflow "Import Material" (Library, unscoped) and
// "Add Material" (Project Record, scoped) both open. Same modal, same
// table, same actions — the only difference is whether scopeProjectId is
// set, which fills in association ONLY when nothing else already
// matched (never overrides real filename/path evidence for a different
// project — see the backend's own comment on this).
//
// Nothing here is canonical until a row's own Commit action runs —
// discovery only ever stages IngestionCandidate rows.

const CATEGORY_OPTIONS = [
  ["screenplay", "Script"], ["budget", "Budget"], ["deck", "Deck"], ["lookbook", "Look Book"],
  ["schedule", "Schedule"], ["pre_qualification", "Pre-Qualification Letter"],
  ["incentive_estimate", "Incentive Estimate"], ["incentive_application", "Incentive Application"],
  ["incentive_certificate", "Incentive Certificate"], ["cost_report", "Cost Report"],
  ["finance", "Finance Plan"], ["cast", "Cast / Talent"], ["crew", "Crew"],
  ["legal", "Legal / Production"], ["artwork", "Artwork"], ["other", "Other"],
];

const VERSION_LABELS = {
  new_document: "New document", exact_duplicate: "Exact duplicate", possible_new_version: "Possible new version",
};

function fmtBytes(n) {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} MB`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)} KB`;
  return `${n} B`;
}

export default function IngestionReviewModal({ scopeProjectId, onClose, onCommitted }) {
  const [source, setSource] = useState(null);
  const [path, setPath] = useState("");
  const [discovering, setDiscovering] = useState(false);
  const [candidates, setCandidates] = useState(null);
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState(null);
  const [rowBusy, setRowBusy] = useState(null);
  const [committedCount, setCommittedCount] = useState(0);

  useEffect(() => {
    getProjects().then(setProjects).catch(() => {});
    refreshCandidates();
  }, []);

  function refreshCandidates() {
    listIngestionCandidates("pending")
      .then((all) => setCandidates(
        // Scoped ("Add Material" on one Project Record): show that
        // project's own candidates plus anything still unassigned, so a
        // low/no-confidence file discovered from this project's own
        // folder is still visible to fix — but hide other projects'
        // already-associated material to keep the scoped review focused.
        scopeProjectId ? all.filter((c) => c.proposed_project_id === scopeProjectId || !c.proposed_project_id) : all
      ))
      .catch((err) => setError(err.message || String(err)));
  }

  async function runDiscover(e) {
    e.preventDefault();
    if (!path.trim()) return;
    setDiscovering(true);
    setError(null);
    try {
      await discoverIngestion(path.trim(), scopeProjectId);
      refreshCandidates();
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setDiscovering(false);
    }
  }

  async function correct(id, changes) {
    setRowBusy(id);
    try {
      const updated = await updateIngestionCandidate(id, changes);
      setCandidates((cur) => cur.map((c) => (c.id === id ? updated : c)));
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setRowBusy(null);
    }
  }

  async function commit(id) {
    setRowBusy(id);
    try {
      await commitIngestionCandidate(id);
      setCandidates((cur) => cur.filter((c) => c.id !== id));
      setCommittedCount((n) => n + 1);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setRowBusy(null);
    }
  }

  async function ignore(id) {
    setRowBusy(id);
    try {
      await ignoreIngestionCandidate(id);
      setCandidates((cur) => cur.filter((c) => c.id !== id));
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setRowBusy(null);
    }
  }

  function close() {
    if (committedCount > 0) onCommitted();
    else onClose();
  }

  return createPortal(
    <div className="np-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) close(); }}>
      <div className="ing-modal">
        <div className="np-head">
          <h2>Import Material</h2>
          <button type="button" className="np-close" onClick={close} aria-label="Close">✕</button>
        </div>

        {source === null ? (
          <IngestionSourceChooser onSelect={setSource} />
        ) : (
        <form className="ing-discover-row" onSubmit={runDiscover}>
          <button type="button" className="ing-source-back" onClick={() => setSource(null)}>
            ← {INGESTION_SOURCES.find((s) => s.key === source)?.label}
          </button>
          <input
            className="field-input"
            type="text"
            placeholder="Absolute folder path on this Mac…"
            value={path}
            onChange={(e) => setPath(e.target.value)}
          />
          <button className="hero-action primary" type="submit" disabled={discovering || !path.trim()}>
            {discovering ? "Scanning…" : "Discover"}
          </button>
        </form>
        )}

        {source !== null && (
        <>
        <p className="text-tertiary small ing-hint">
          Reads files from a folder on this Mac. Nothing becomes part of a Project until you Commit a row below.
        </p>

        {error && <p className="np-error">{error}</p>}

        {candidates === null ? (
          <p className="text-tertiary small">Loading…</p>
        ) : candidates.length === 0 ? (
          <div className="empty-state">No pending material to review. Discover a folder above.</div>
        ) : (
          <div className="ing-table-wrap">
            <table className="ing-table">
              <thead>
                <tr>
                  <th>File</th><th>Type</th><th>Project</th><th>Version</th><th>Confidence</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <div className="ing-fname">{c.filename}</div>
                      <div className="text-tertiary" style={{ fontSize: 10.5 }}>{fmtBytes(c.file_size)}</div>
                    </td>
                    <td>
                      <select
                        className="field-select ing-select"
                        value={c.proposed_category}
                        disabled={rowBusy === c.id}
                        onChange={(e) => correct(c.id, { proposed_category: e.target.value })}
                      >
                        {CATEGORY_OPTIONS.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
                      </select>
                    </td>
                    <td>
                      <select
                        className="field-select ing-select"
                        value={c.proposed_project_id || ""}
                        disabled={rowBusy === c.id}
                        onChange={(e) => correct(c.id, { proposed_project_id: e.target.value || null })}
                      >
                        <option value="">— Select project —</option>
                        {projects.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
                      </select>
                    </td>
                    <td>
                      <span className={`ing-version ${c.version_status}`}>{VERSION_LABELS[c.version_status] || c.version_status}</span>
                    </td>
                    <td>
                      <span className={`ing-conf ing-conf-${c.category_confidence}`}>cat: {c.category_confidence}</span>
                      <span className={`ing-conf ing-conf-${c.association_confidence}`}>proj: {c.association_confidence}</span>
                    </td>
                    <td className="ing-actions">
                      <button
                        className="hero-action primary small"
                        disabled={rowBusy === c.id || !c.proposed_project_id}
                        title={!c.proposed_project_id ? "Select a project first" : undefined}
                        onClick={() => commit(c.id)}
                      >
                        Commit
                      </button>
                      <button className="hero-action small" disabled={rowBusy === c.id} onClick={() => ignore(c.id)}>Ignore</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {committedCount > 0 && (
          <p className="text-tertiary small" style={{ marginTop: 8 }}>{committedCount} committed this session.</p>
        )}
        </>
        )}
      </div>
    </div>,
    document.body,
  );
}
