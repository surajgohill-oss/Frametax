import { useState } from "react";
import { useAppState } from "../state/AppState";
import { Money } from "../lib/format";

const GROUPS = [
  { key: "financial", label: "Financial" },
  { key: "structural", label: "Structural" },
  { key: "creative", label: "Creative" },
  { key: "legal", label: "Legal / Evidence" },
];

export default function RecommendationsList({ byCategory, legal, compact = false }) {
  const [group, setGroup] = useState("financial");
  const { openInspector } = useAppState();
  const items = group === "legal" ? legal : byCategory[group];
  const shown = compact ? items.slice(0, 5) : items;

  return (
    <div>
      <div className="tag-row">
        {GROUPS.map((g) => (
          <button
            key={g.key}
            className={`tag ${group === g.key ? "active" : ""}`}
            onClick={() => setGroup(g.key)}
          >
            {g.label} <span className="text-tertiary">{(g.key === "legal" ? legal : byCategory[g.key]).length}</span>
          </button>
        ))}
      </div>
      {shown.length === 0 ? (
        <p className="empty-state">No {group} recommendations right now.</p>
      ) : (
        <div className="row-list">
          {shown.map((r) => (
            <div key={r.recommendation_id} className="row-item recommendation-row" onClick={() => openInspector("recommendation", r)}>
              <span className={`dot ${r.confidence === "high" ? "jade" : r.confidence === "medium" ? "silver" : "amber"}`} />
              <div className="row-main">
                <div className="row-title">{r.title}</div>
                {r.description && <div className="row-description">{r.description}</div>}
                <div className="row-sub">
                  {r.jurisdiction_codes?.length > 0 && <span className="mono">{r.jurisdiction_codes.join(" · ")}</span>}
                  {r.jurisdiction_codes?.length > 0 && " — "}
                  {r.requires_counsel_approval ? "Counsel approval required" : "Producer approval"}
                  {r.creative_impact ? " · creative change" : ""}
                </div>
              </div>
              <div className="row-value"><Money value={r.estimated_value_usd} /></div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
