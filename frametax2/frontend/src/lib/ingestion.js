// Shared across Binder.jsx and Overview.jsx's ProductionIntake — the same
// real gap, stated once. POST /api/v1/documents/upload works and persists
// via SQLAlchemy, but little_utopia_state.py serves a static in-memory
// production disconnected from that documents table, so an upload would
// succeed but never appear anywhere in this app. Disabled everywhere until
// that read path exists — never presented as working in one place and
// disclosed as broken in another.
export const UPLOAD_BLOCKED_REASON =
  "POST /api/v1/documents/upload exists and works (accepts PDF/CSV/XLSX/FDX, persists via SQLAlchemy), " +
  "but little_utopia_state.py serves a static in-memory production disconnected from the SQL documents table " +
  "it writes to — an upload would succeed but never appear here. Disabled until that read path exists.";

export const DRIVE_BLOCKED_REASON =
  "No Google Drive OAuth connector is wired into this backend yet. This is a designed integration point, " +
  "not a working connection — wiring it requires a Drive API credential and a picker flow, out of scope for " +
  "a frontend-only pass.";

export const GMAIL_BLOCKED_REASON =
  "No Gmail connector is wired into this backend yet. This is a designed integration point for pulling budget/" +
  "script attachments directly from a producer's inbox — wiring it requires Gmail API access, out of scope for " +
  "a frontend-only pass.";
