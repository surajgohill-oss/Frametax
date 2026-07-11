import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import FXStrip from "../../components/FXStrip";
import RecommendationsList from "../../components/RecommendationsList";
import QuestionStack from "../../components/QuestionStack";

export default function Overview() {
  const { data, error, loading } = useCineGlobe();
  const navigate = useNavigate();
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, recommendations, structures, legal } = data;
  const baseline = structures.candidates.find((c) => c.candidate_id === `PSC-${production.jurisdiction_code}`);
  const npc = baseline?.cases?.risk_adjusted?.net_production_cost_usd;
  const best = structures.ranking.find((r) => r.is_priceable);

  return (
    <div className="screen">
      <section className="overview-hero">
        <div className="overview-hero-art" aria-hidden="true" />
        <div>
          <p className="screen-eyebrow">Feature · {pkg.confidence} confidence</p>
          <h1 className="serif overview-title">{production.production_name}</h1>
          <p className="text-secondary overview-logline">
            An account-level production package structured under the Mauritius EDB Film Rebate Scheme.
          </p>
          <div className="overview-stats">
            <div>
              <span className="text-tertiary small">Total production budget</span>
              <div className="mono overview-stat-value"><Money value={production.gross_budget_usd} /></div>
            </div>
            <div>
              <span className="text-tertiary small">Best jurisdiction</span>
              <div className="mono overview-stat-value">{best?.label || production.jurisdiction_code}</div>
            </div>
            <div>
              <span className="text-tertiary small">Net production cost</span>
              <div className="mono overview-stat-value"><Money value={npc} /></div>
            </div>
          </div>
        </div>
      </section>

      <FXStrip />

      <div className="overview-regions">
        <section className="region">
          <div className="region-title">Open Questions <span className="count">{pkg.missing_inputs.length}</span></div>
          <QuestionStack missingInputs={pkg.missing_inputs.slice(0, 5)} greyAreas={[]} />
          <button className="link-more" onClick={() => navigate("/production/workspace")}>Open Workspace →</button>
        </section>

        <section className="region">
          <div className="region-title">Scenarios <span className="count">{structures.candidates.length}</span></div>
          <div className="row-list">
            {structures.ranking.slice(0, 4).map((r) => (
              <div className="row-item" key={r.structure_id} onClick={() => navigate("/production/workspace")}>
                <span className={`dot ${r.is_priceable ? "gold" : "charcoal"}`} />
                <div className="row-main">
                  <div className="row-title">{r.label}</div>
                </div>
                <div className="row-value"><Money value={r.risk_adjusted_npc_usd} /></div>
              </div>
            ))}
          </div>
        </section>

        <section className="region">
          <div className="region-title">Production Sheet</div>
          <dl className="kv-list">
            <div><dt>Line items</dt><dd>{pkg.budget.line_item_count}</dd></div>
            <div><dt>ATL</dt><dd><Money value={pkg.budget.atl_total_usd} /></dd></div>
            <div><dt>BTL</dt><dd><Money value={pkg.budget.btl_total_usd} /></dd></div>
            <div><dt>Post</dt><dd><Money value={pkg.budget.post_total_usd} /></dd></div>
          </dl>
          <button className="link-more" onClick={() => navigate("/production/binder")}>Open Production Sheet →</button>
        </section>

        <section className="region">
          <div className="region-title">Latest Record</div>
          {legal.committed_rule_id ? (
            <p className="small text-secondary">
              {legal.grey_areas_current.find((g) => g.graph_rule_id === legal.committed_rule_id)?.item_id} resolved via
              committed authority — Authority Score {legal.authority_scores[legal.committed_rule_id]?.composite}/100.
            </p>
          ) : (
            <p className="empty-state">No record entries yet.</p>
          )}
          <button className="link-more" onClick={() => navigate("/production/record")}>Open Record →</button>
        </section>

        <section className="region overview-region-wide">
          <div className="region-title">Intelligence</div>
          <RecommendationsList byCategory={recommendations.by_category} legal={recommendations.legal} compact />
        </section>
      </div>
    </div>
  );
}
