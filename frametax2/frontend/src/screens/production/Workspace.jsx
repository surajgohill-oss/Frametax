import { useMemo, useState } from "react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, Pct } from "../../lib/format";
import { useAppState } from "../../state/AppState";
import Globe3D from "../../components/Globe3D";
import { JURISDICTION_COORDS } from "../../lib/jurisdictions";
import QuestionStack from "../../components/QuestionStack";
import RecommendationsList from "../../components/RecommendationsList";
import EconomicsTrace from "../../components/EconomicsTrace";

const MODES = [
  { key: "lanes", label: "Lanes" },
  { key: "map", label: "Map" },
  { key: "recommendations", label: "Recommendations" },
  { key: "questions", label: "Questions" },
];

function candidateTier(candidate, rankIndex) {
  if (candidate.is_fully_priced && rankIndex === 0) return "gold";
  if (candidate.is_fully_priced) return "jade";
  if (candidate.constraints.length > 0) return "amber";
  return "silver";
}

function JurisdictionLane({ candidate, tier, onSelect }) {
  const cases = candidate.cases || {};
  return (
    <div className={`lane lane-${tier}`} onClick={onSelect}>
      <div className="lane-header">
        <span className={`dot ${tier}`} />
        <span className="lane-title">{candidate.label}</span>
      </div>
      <div className="lane-sub text-tertiary small">Priceable <Pct value={candidate.priceable_pct} /></div>
      {Object.keys(cases).length > 0 ? (
        <table className="inspector-table">
          <tbody>
            {["conservative", "base", "optimistic", "risk_adjusted"].filter((k) => cases[k]).map((k) => (
              <tr key={k}><td>{k.replace("_", " ")}</td><td className="mono"><Money value={cases[k].net_production_cost_usd} /></td></tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="text-tertiary small">Unpriced — no register for this set.</p>
      )}
      {candidate.constraints.length > 0 && (
        <p className="text-tertiary small">{candidate.constraints.length} open constraint(s)</p>
      )}
    </div>
  );
}

export default function Workspace() {
  const { data, error, loading } = useCineGlobe();
  const [mode, setMode] = useState("lanes");
  const [activeGreyArea, setActiveGreyArea] = useState(null);
  const { openInspector } = useAppState();

  const points = useMemo(() => {
    if (!data) return [];
    return data.structures.candidates
      .map((c, unusedIdx) => {
        const code = c.participating_jurisdictions.find((j) => j !== data.production.jurisdiction_code) || data.production.jurisdiction_code;
        const coord = JURISDICTION_COORDS[code];
        if (!coord) return null;
        const rankIndex = data.structures.ranking.findIndex((r) => r.structure_id === c.candidate_id);
        return { lat: coord.lat, lng: coord.lng, tier: candidateTier(c, rankIndex), name: c.label, id: c.candidate_id };
      })
      .filter(Boolean);
  }, [data]);

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, structures, recommendations, legal } = data;
  const best = structures.ranking.find((r) => r.is_priceable);

  return (
    <div className="workspace-screen">
      <div className="workspace-verdict">
        <span className="dot gold" />
        <span>Best current structure: <strong>{best?.label}</strong></span>
        <span className="text-tertiary">·</span>
        <span className="mono"><Money value={best?.risk_adjusted_npc_usd} /> risk-adjusted NPC</span>
      </div>

      <div className="workspace-body">
        <aside className="production-rail">
          <div className="region">
            <div className="region-title">Production</div>
            <dl className="kv-list">
              <div><dt>Gross budget</dt><dd><Money value={production.gross_budget_usd} /></dd></div>
              <div><dt>Rate</dt><dd className="mono">{(production.rate * 100).toFixed(0)}%</dd></div>
              <div><dt>ATL</dt><dd><Money value={pkg.budget.atl_total_usd} /></dd></div>
              <div><dt>BTL</dt><dd><Money value={pkg.budget.btl_total_usd} /></dd></div>
              <div><dt>Post</dt><dd><Money value={pkg.budget.post_total_usd} /></dd></div>
            </dl>
          </div>
          <div className="region">
            <div className="region-title">Opportunity hints <span className="count">{pkg.budget.opportunity_hints.length}</span></div>
            <div className="row-list">
              {pkg.budget.opportunity_hints.slice(0, 4).map((h) => (
                <div key={h.hint_id} className="hint-row">
                  <span className="text-tertiary small">{h.category}</span>
                  <p className="small" style={{ margin: "2px 0 0" }}>{h.description}</p>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <div className="workspace-canvas">
          <nav className="mode-tabs">
            {MODES.map((m) => (
              <button key={m.key} className={mode === m.key ? "active" : ""} onClick={() => setMode(m.key)}>{m.label}</button>
            ))}
          </nav>

          {mode === "lanes" && (
            <div className="lanes-row scroll-x">
              {structures.candidates.map((c) => {
                const rankIndex = structures.ranking.findIndex((r) => r.structure_id === c.candidate_id);
                return (
                  <JurisdictionLane
                    key={c.candidate_id}
                    candidate={c}
                    tier={candidateTier(c, rankIndex)}
                    onSelect={() => openInspector("candidate", c)}
                  />
                );
              })}
            </div>
          )}

          {mode === "map" && (
            <div className="globe-canvas-wrap">
              <Globe3D points={points} height={480} onPointClick={(pt) => {
                const c = structures.candidates.find((cand) => cand.candidate_id === pt.id);
                if (c) openInspector("candidate", c);
              }} />
              <p className="text-tertiary small">
                Recommendation Mode — gold: best priced structure · jade: priced alternative ·
                amber: gated on missing register/authority · silver: viable, unpriced. No treaty
                arcs shown — current candidates carry no treaty compositions.
              </p>
            </div>
          )}

          {mode === "recommendations" && (
            <div className="region">
              <RecommendationsList byCategory={recommendations.by_category} legal={recommendations.legal} />
            </div>
          )}

          {mode === "questions" && (
            <div className="region">
              <QuestionStack
                missingInputs={pkg.missing_inputs}
                greyAreas={legal.grey_areas_current}
              />
              <div className="trace-trigger-row">
                {legal.grey_areas_current.map((g) => (
                  <button key={g.item_id} className={`tag ${activeGreyArea?.item_id === g.item_id ? "active" : ""}`} onClick={() => setActiveGreyArea(g)}>
                    Trace {g.item_id}
                  </button>
                ))}
              </div>
              {activeGreyArea && <EconomicsTrace greyArea={activeGreyArea} legal={legal} />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
