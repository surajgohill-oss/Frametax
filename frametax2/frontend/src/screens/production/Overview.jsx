import { useNavigate } from "react-router-dom";
import { LayoutDashboard, FolderOpen } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money } from "../../lib/format";
import FXStrip from "../../components/FXStrip";
import RecommendationsList from "../../components/RecommendationsList";
import QuestionStack from "../../components/QuestionStack";
import QualificationPanel from "../../components/QualificationPanel";
import QualificationAssistant from "../../components/QualificationAssistant";
import ProductionIntake from "../../components/ProductionIntake";

export default function Overview() {
  const { data, error, loading, refetch } = useCineGlobe();
  const navigate = useNavigate();
  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, recommendations, structures, legal, people, facts, economics } = data;
  const baseline = structures.candidates.find((c) => c.candidate_id === `PSC-${production.jurisdiction_code}`);
  const npc = baseline?.cases?.risk_adjusted?.net_production_cost_usd;
  const best = structures.ranking.find((r) => r.is_priceable);

  return (
    <div className="screen">
      <section className="overview-hero">
        <div className="overview-hero-art" aria-hidden="true" />
        <div className="overview-hero-body">
          <div style={{ display: "flex", alignItems: "flex-start" }}>
            <div>
              <p className="screen-eyebrow">Feature · {pkg.confidence} confidence</p>
              <h1 className="serif overview-title">{production.production_name}</h1>
            </div>
            <div className="overview-hero-actions">
              <button className="hero-action" onClick={() => navigate("/production/workspace")}>
                <FolderOpen size={14} strokeWidth={1.8} /> New scenario
              </button>
              <button className="hero-action primary" onClick={() => navigate("/production/workspace")}>
                <LayoutDashboard size={14} strokeWidth={1.8} /> Open Workspace
              </button>
            </div>
          </div>
          <p className="overview-logline">
            An account-level production package structured under the Mauritius EDB Film Rebate Scheme.
          </p>
          <div className="overview-stats">
            <div>
              <span className="text-tertiary small">Total production budget</span>
              <div className="mono overview-stat-value"><Money value={production.gross_budget_usd} /></div>
            </div>
            <div>
              <span className="text-tertiary small">Recommended structure</span>
              <div className="mono overview-stat-value">{best?.label || production.jurisdiction_code}</div>
            </div>
            <div>
              <span className="text-tertiary small">Risk-adjusted net production cost</span>
              <div className="mono overview-stat-value"><Money value={npc} /></div>
            </div>
          </div>
        </div>
      </section>

      <FXStrip economics={economics} />

      <QualificationAssistant allocatedStructures={structures.allocated_structures} recommendations={recommendations} />

      <div className="overview-sheet">
        <div className="overview-sheet-col">
          <ProductionIntake />

          <QualificationPanel people={people} facts={facts} script={pkg.script} refetch={refetch} />

          <section className="region region-conditional">
            <div className="region-title"><span>Open Questions</span><span className="count">{pkg.missing_inputs.length}</span></div>
            <QuestionStack missingInputs={pkg.missing_inputs.slice(0, 5)} greyAreas={[]} />
            <button className="link-more" onClick={() => navigate("/production/workspace")}>Open Workspace →</button>
          </section>

          <section className="region">
            <div className="region-title"><span>Production Sheet</span></div>
            <dl className="kv-list">
              <div><dt>Line items</dt><dd className="mono">{pkg.budget.line_item_count}</dd></div>
              <div><dt>Above the line</dt><dd><Money value={pkg.budget.atl_total_usd} /></dd></div>
              <div><dt>Below the line</dt><dd><Money value={pkg.budget.btl_total_usd} /></dd></div>
              <div><dt>Post production</dt><dd><Money value={pkg.budget.post_total_usd} /></dd></div>
            </dl>
            <button className="link-more" onClick={() => navigate("/production/binder")}>Open Production Sheet →</button>
          </section>
        </div>

        <div className="overview-sheet-col">
          <section className="region region-warm">
            <div className="region-title"><span>Scenarios</span><span className="count">{structures.candidates.length}</span></div>
            <div className="row-list">
              {structures.ranking.slice(0, 4).map((r) => (
                <div className="row-item" key={r.structure_id} onClick={() => navigate("/production/workspace")}>
                  <span className={`dot ${r.is_priceable ? "gold" : "charcoal"}`} />
                  <div className="row-main">
                    <div className="row-title" style={{ fontWeight: 400 }}>{r.label.replace(/^Relocate /, "").replace(/ -> /g, " → ")}</div>
                  </div>
                  <div className="row-value mono">{r.is_priceable ? <Money value={r.risk_adjusted_npc_usd} /> : <span className="text-tertiary small">not yet priced</span>}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="region region-positive">
            <div className="region-title"><span>Latest Record</span></div>
            {legal.committed_rule_id ? (
              <p className="small" style={{ color: "var(--text-secondary)", lineHeight: 1.6 }}>
                {legal.grey_areas_current.find((g) => g.graph_rule_id === legal.committed_rule_id)?.resolving_evidence} — resolved
                with Authority Score {legal.authority_scores[legal.committed_rule_id]?.composite}/100.
              </p>
            ) : (
              <p className="empty-state">No record entries yet.</p>
            )}
            <button className="link-more" onClick={() => navigate("/production/record")}>Open Record →</button>
          </section>

          <section className="region">
            <div className="region-title"><span>Intelligence</span></div>
            <RecommendationsList byCategory={recommendations.by_category} legal={recommendations.legal} compact />
          </section>
        </div>
      </div>
    </div>
  );
}
