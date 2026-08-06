// Shared source-choice UI — "Import Material" (Library), "Add Material"
// (Project Record), and "+ New Project" (material-based creation) all
// render this same chooser, same copy, same behavior. CineGlobe reads
// from disk BY PATH, not a browser upload — there is no separate
// "upload individual files" backend capability, and building one just
// for one entry point would be a second ingestion path. "Local Folder"
// and "Local Files" both resolve to the same discoverIngestion(path)
// call for that reason; the copy under "Local Files" says so rather
// than implying an upload picker that doesn't exist. Google Drive has
// no backend connector yet — shown disabled rather than faked.
export const INGESTION_SOURCES = [
  { key: "folder", label: "Local Folder", desc: "Point at a folder on this Mac — every file inside is discovered." },
  { key: "files", label: "Local Files", desc: "Enter the folder containing the specific file(s) — CineGlobe reads by path, not browser upload." },
  { key: "drive", label: "Google Drive", desc: "Connect / Unavailable — no Drive connector is wired up yet.", disabled: true },
];

export default function IngestionSourceChooser({ heading = "Import from", extraOptions = [], onSelect }) {
  const options = [...INGESTION_SOURCES, ...extraOptions];
  return (
    <div className="ing-source-chooser">
      <p className="text-tertiary small ing-hint">{heading}</p>
      {options.map((s) => (
        <button
          key={s.key}
          type="button"
          className={`ing-source-option ${s.disabled ? "disabled" : ""}`}
          disabled={s.disabled}
          onClick={() => onSelect(s.key)}
        >
          <span className="ing-source-label">{s.label}</span>
          <span className="ing-source-desc">{s.desc}</span>
        </button>
      ))}
    </div>
  );
}
