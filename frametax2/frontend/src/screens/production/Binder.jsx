import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";

export default function Binder() {
  const { data, error, loading } = useCineGlobe();
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { legal } = data;
  const documents = legal.evidence_trace; // real Document/DocumentVersion/AuthoritySource records
  const pendingItems = legal.grey_areas_current.filter((g) => g.status === "open");

  return (
    <div className="screen">
      <header className="screen-header">
        <p className="screen-eyebrow">Production Binder</p>
        <h1 className="screen-title">Documents &amp; authority</h1>
        <p className="text-tertiary small">Source: {legal.connector_source_label}</p>
      </header>

      <section className="region">
        <div className="region-title">Committed documents <span className="count">{documents.length}</span></div>
        {documents.length === 0 ? (
          <p className="empty-state">No document has been committed to the Evidence Graph yet.</p>
        ) : (
          <div className="row-list">
            {documents.map((d) => {
              const isMockSource = (d.document_source_url || "").startsWith("mock://");
              return (
                <div key={d.evidence_id} className="row-item binder-row">
                  <div className="binder-doc-icon" aria-hidden="true">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                      <path d="M6 2h9l5 5v15H6z" stroke="currentColor" strokeWidth="1.3" />
                      <path d="M15 2v5h5" stroke="currentColor" strokeWidth="1.3" />
                    </svg>
                  </div>
                  <div className="row-main">
                    <div className="binder-doc-header">
                      <div className="row-title">{d.document_title}</div>
                      {isMockSource && <span className="badge amber">unverified source</span>}
                    </div>
                    <div className="row-sub">
                      <span className="mono">{d.authority_tier.replace(/_/g, " ").toLowerCase()}</span> · {d.authority_body} ·
                      retrieved {d.retrieved_date} · version {d.document_version_label}
                    </div>
                    <p className="small text-secondary" style={{ marginTop: 6 }}>{d.citation_text}</p>
                  </div>
                  <div className="binder-actions">
                    {isMockSource ? (
                      <span className="ghost-action small" title="No live document is attached — this citation is a MockConnector placeholder">Open original</span>
                    ) : (
                      <a href={d.document_source_url} target="_blank" rel="noreferrer" className="link-more">Open original</a>
                    )}
                    <span className="ghost-action small">Run OCR</span>
                    <span className="ghost-action small">Rerun extraction</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="region">
        <div className="region-title">Pending — no document yet <span className="count">{pendingItems.length}</span></div>
        <div className="row-list">
          {pendingItems.map((g) => (
            <div className="row-item" key={g.item_id}>
              <span className="dot amber" />
              <div className="row-main">
                <div className="row-title">{g.item_id}</div>
                <div className="row-sub">Required: {g.resolving_evidence}</div>
              </div>
              <span className="ghost-action small">Attach document</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
