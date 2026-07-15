import { useState } from "react";
import { Upload, FolderSync, Mail } from "lucide-react";
import { UPLOAD_BLOCKED_REASON, DRIVE_BLOCKED_REASON, GMAIL_BLOCKED_REASON } from "../lib/ingestion";

// Intake UI for Production Overview. Mirrors Binder.jsx's own disabled
// upload controls exactly — same reason text, same disabled state — so
// this is one ingestion surface with two entry points, not a second
// pipeline. Drag/drop is visually real (dragover highlight) but inert for
// the same reason: the upload endpoint works, the demo state can't read
// from it yet.
export default function ProductionIntake() {
  const [dragging, setDragging] = useState(false);

  return (
    <section className="region">
      <div className="region-title"><span>Production Intake</span></div>
      <div
        className="field-row"
        style={{
          flexDirection: "column", alignItems: "center", justifyContent: "center",
          gap: 6, padding: "24px 12px", border: `1px dashed ${dragging ? "var(--blue)" : "var(--hairline-strong)"}`,
          borderRadius: "var(--radius-md)", background: dragging ? "var(--surface-cool)" : "transparent",
        }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); }}
        title={UPLOAD_BLOCKED_REASON}
      >
        <Upload size={18} strokeWidth={1.6} color="var(--text-tertiary)" />
        <span className="text-tertiary small">Drag a budget or script here, or use a source below</span>
      </div>
      <div className="tag-row" style={{ marginTop: 10 }}>
        <button className="tag" disabled title={UPLOAD_BLOCKED_REASON}>
          <Upload size={12} strokeWidth={1.8} style={{ marginRight: 4 }} /> From computer
        </button>
        <button className="tag" disabled title={DRIVE_BLOCKED_REASON}>
          <FolderSync size={12} strokeWidth={1.8} style={{ marginRight: 4 }} /> Google Drive
        </button>
        <button className="tag" disabled title={GMAIL_BLOCKED_REASON}>
          <Mail size={12} strokeWidth={1.8} style={{ marginRight: 4 }} /> Gmail attachments
        </button>
      </div>
      <p className="field-unavailable" style={{ marginTop: 8, display: "block" }}>
        Upload persists via the real documents pipeline (POST /api/v1/documents/upload) but this demo production
        isn't yet wired to read from it — see Production Binder for the same disclosure.
      </p>
    </section>
  );
}
