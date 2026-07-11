import { useState } from "react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";

const SCOPES = ["Production", "Jurisdiction", "Company"];

export default function Knowledge() {
  const { data, error, loading } = useCineGlobe();
  const [scope, setScope] = useState("Production");
  const [selected, setSelected] = useState(null);
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { legal, production } = data;
  const entries = legal.grey_areas_current;
  const active = selected || entries[0];

  return (
    <div className="screen">
      <header className="screen-header">
        <p className="screen-eyebrow">Knowledge</p>
        <h1 className="screen-title">The Little Utopia</h1>
      </header>

      <div className="tag-row">
        {SCOPES.map((s) => (
          <button key={s} className={`tag ${scope === s ? "active" : ""}`} onClick={() => setScope(s)}>{s}</button>
        ))}
      </div>
      <p className="text-tertiary small" style={{ margin: "8px 0 20px" }}>
        {scope === "Production" && "Knowledge attached directly to The Little Utopia."}
        {scope === "Jurisdiction" && `Knowledge scoped to ${production.jurisdiction_code} — currently identical to production scope, since this is the only jurisdiction with committed knowledge.`}
        {scope === "Company" && "Knowledge visible across the whole portfolio — currently only The Little Utopia contributes."}
      </p>

      <div className="split-pane">
        <div className="row-list" style={{ width: 320, flexShrink: 0 }}>
          {entries.map((e) => (
            <div key={e.item_id} className={`row-item ${active?.item_id === e.item_id ? "active" : ""}`} onClick={() => setSelected(e)}>
              <span className={`dot ${e.status === "open" ? "amber" : "jade"}`} />
              <div className="row-main">
                <div className="row-title">{e.item_id}</div>
                <div className="row-sub">{e.status.replace("_", " ")}</div>
              </div>
            </div>
          ))}
        </div>

        {active && (
          <div className="region" style={{ flex: 1 }}>
            <div className="region-title">{active.item_id}</div>
            <dl className="kv-list">
              <div><dt>Issue</dt><dd style={{ maxWidth: 380, textAlign: "right" }}>{active.authority_to_ask}</dd></div>
              <div><dt>Evidence</dt><dd style={{ maxWidth: 380, textAlign: "right" }}>{active.resolving_evidence}</dd></div>
              <div><dt>Confidence</dt><dd>{legal.authority_scores[active.graph_rule_id]?.confidence || "Unresolved"}</dd></div>
              <div><dt>Business impact</dt><dd><Money value={active.amount_usd} /></dd></div>
              <div><dt>Affected jurisdictions</dt><dd>{active.jurisdiction_code}</dd></div>
              <div><dt>Authority</dt><dd>{active.graph_rule_id || "AbsenceOfAuthority (not yet resolved)"}</dd></div>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
