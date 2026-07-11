import { FileText, ExternalLink, ScanText, RefreshCw, Paperclip } from "lucide-react";
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

      <section className="region region-cool">
        <div className="region-title"><span>Committed documents</span><span className="count">{documents.length}</span></div>
        {documents.length === 0 ? (
          <p className="empty-state">No document has been committed to the Evidence Graph yet.</p>
        ) : (
          <div className="row-list">
            {documents.map((d) => {
              const isMockSource = (d.document_source_url || "").startsWith("mock://");
              return (
                <div key={d.evidence_id} className="row-item binder-row">
                  <div className="binder-doc-icon" aria-hidden="true">
                    <FileText size={16} strokeWidth={1.7} />
                  </div>
                  <div className="row-main">
                    <div className="binder-doc-header">
                      <div className="row-title">{d.document_title}</div>
                      {isMockSource && <span className="badge amber">demonstration data — unverified</span>}
                    </div>
                    <div className="row-sub">
                      <span className="mono">{d.authority_tier.replace(/_/g, " ").toLowerCase()}</span> · {d.authority_body} ·
                      retrieved {d.retrieved_date} · version {d.document_version_label}
                    </div>
                    <p className="small text-secondary" style={{ marginTop: 6 }}>{d.citation_text}</p>
                  </div>
                  <div className="binder-actions">
                    {isMockSource ? (
                      <span className="ghost-action small" title="No live document is attached — this citation is a MockConnector placeholder">
                        <ExternalLink size={12} /> Open original
                      </span>
                    ) : (
                      <a href={d.document_source_url} target="_blank" rel="noreferrer" className="link-more">
                        <ExternalLink size={12} /> Open original
                      </a>
                    )}
                    <span className="ghost-action small"><ScanText size={12} /> Run OCR</span>
                    <span className="ghost-action small"><RefreshCw size={12} /> Rerun extraction</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="region region-conditional">
        <div className="region-title"><span>Pending — no document yet</span><span className="count">{pendingItems.length}</span></div>
        <div className="row-list">
          {pendingItems.map((g) => (
            <div className="row-item" key={g.item_id}>
              <span className="dot amber" />
              <div className="row-main">
                <div className="row-title">{g.resolving_evidence}</div>
                <div className="row-sub">{g.authority_to_ask} · {g.jurisdiction_code}</div>
              </div>
              <span className="ghost-action small"><Paperclip size={12} /> Attach document</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
