import { useMemo, useState } from "react";
import { Rows3, Globe2, Columns2, ChevronDown } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, Pct, structureLabel, accountStateLabel } from "../../lib/format";
import { buildAccountBlocks } from "../../lib/budgetBlocks";
import { useAppState } from "../../state/AppState";
import Globe3D from "../../components/Globe3D";
import { JURISDICTION_COORDS } from "../../lib/jurisdictions";
import QuestionStack from "../../components/QuestionStack";
import RecommendationsList from "../../components/RecommendationsList";
import EconomicsTrace from "../../components/EconomicsTrace";

const MODES = [
  { key: "lanes", label: "Lanes", icon: Rows3 },
  { key: "map", label: "Map", icon: Globe2 },
  { key: "split", label: "Split", icon: Columns2 },
];

function candidateTier(candidate, rankIndex) {
  if (candidate.is_fully_priced && rankIndex === 0) return "gold";
  if (candidate.is_fully_priced) return "jade";
  if (candidate.constraints.length > 0) return "amber";
  return "silver";
}

function ModelRailBlock({ block, maxAmount, onSelectAccount }) {
  const [open, setOpen] = useState(false);
  const pct = Math.min(100, Math.round((block.amount / maxAmount) * 100));
  return (
    <div className="budget-block">
      <div className="budget-block-header" onClick={() => setOpen((o) => !o)}>
        <span className="budget-block-name">{block.label}</span>
        <span className="budget-block-amount mono"><Money value={block.amount} /></span>
      </div>
      <div className="budget-block-bar"><div className="budget-block-bar-fill" style={{ width: `${pct}%` }} /></div>
      {open && (
        <div className="budget-block-lines">
          {block.lines.map((l) => {
            const state = accountStateLabel(l.state);
            return (
              <div className="budget-line" key={l.key} onClick={(e) => { e.stopPropagation(); onSelectAccount(l); }}>
                <span className="budget-line-name">
                  <span className={`dot ${state.tier}`} />
                  {l.label}
                  {l.movement !== "unclassified" && <span className={`movement-chip ${l.movement}`}>{l.movement}</span>}
                </span>
                <span className="mono"><Money value={l.amount} /></span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function JurisdictionLane({ candidate, tier, onSelect }) {
  const cases = candidate.cases || {};
  const baseCase = cases.base;
  const pctLabel = `${Math.round(candidate.priceable_pct * 100)}%`;
  return (
    <div className={`lane lane-${tier}`} onClick={onSelect}>
      <div className="lane-header">
        <span className="lane-title">{structureLabel(candidate.participating_jurisdictions)}</span>
        <span className={`dot ${tier}`} />
      </div>
      <p className="lane-sub text-tertiary small">{pctLabel} of this structure can currently be priced</p>

      {candidate.is_fully_priced && baseCase ? (
        <>
          <div className="lane-metric-row"><span className="label">Qualifying spend</span><span className="mono"><Money value={baseCase.qpe_usd} /></span></div>
          <div className="lane-metric-row"><span className="label">Incentive value</span><span className="mono"><Money value={baseCase.incentive_usd} /></span></div>
          <div className="lane-metric-row"><span className="label">Finance cost</span><span className="mono"><Money value={baseCase.finance_cost_usd} /></span></div>
          <div className="lane-metric-row"><span className="label">Net production cost</span><span className="mono"><Money value={baseCase.net_production_cost_usd} /></span></div>
        </>
      ) : (
        <>
          <p className="lane-partial-note">
            {Math.round(candidate.priceable_pct * 100)}% of this structure can currently be priced — the rest depends on{" "}
            {candidate.constraints.length} unresolved requirement{candidate.constraints.length === 1 ? "" : "s"}, mostly
            authority decisions for the added jurisdiction. A full cost comparison isn't available until those are resolved.
          </p>
          {candidate.informational_upside_usd != null ? (
            <div className="lane-metric-row" style={{ marginTop: 8 }}>
              <span className="label">Estimated routing opportunity</span>
              <span className="mono"><Money value={candidate.informational_upside_usd} /></span>
            </div>
          ) : (
            <p className="lane-sub text-tertiary small" style={{ marginTop: 8 }}>
              No quantifiable rate advantage identified for this jurisdiction against the Mauritius baseline in current
              program data.
            </p>
          )}
        </>
      )}
    </div>
  );
}

export default function Workspace() {
  const { data, error, loading } = useCineGlobe();
  const [mode, setMode] = useState("lanes");
  const [sideTab, setSideTab] = useState("questions");
  const [activeGreyArea, setActiveGreyArea] = useState(null);
  const { openInspector } = useAppState();

  const points = useMemo(() => {
    if (!data) return [];
    return data.structures.candidates
      .map((c) => {
        const code = c.participating_jurisdictions.find((j) => j !== data.production.jurisdiction_code) || data.production.jurisdiction_code;
        const coord = JURISDICTION_COORDS[code];
        if (!coord) return null;
        const rankIndex = data.structures.ranking.findIndex((r) => r.structure_id === c.candidate_id);
        return { lat: coord.lat, lng: coord.lng, tier: candidateTier(c, rankIndex), name: c.label, id: c.candidate_id };
      })
      .filter(Boolean);
  }, [data]);

  const budgetBlocks = useMemo(() => (data ? buildAccountBlocks(data.pkg.register) : []), [data]);
  const maxBlockAmount = useMemo(() => Math.max(1, ...budgetBlocks.map((b) => b.amount)), [budgetBlocks]);

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
        <span className="mono"><Money value={best?.risk_adjusted_npc_usd} /> risk-adjusted net production cost</span>
      </div>

      <div className="workspace-body">
        <aside className="model-rail">
          <p className="model-rail-heading">Model Rail — production budget</p>
          <div className="rail-total">
            <span className="text-tertiary small">Gross budget</span>
            <span className="amount mono"><Money value={production.gross_budget_usd} /></span>
          </div>
          {budgetBlocks.map((block) => (
            <ModelRailBlock
              key={block.key}
              block={block}
              maxAmount={maxBlockAmount}
              onSelectAccount={(line) => openInspector("account", line)}
            />
          ))}
        </aside>

        <div className="workspace-canvas">
          <nav className="mode-tabs">
            {MODES.map((m) => {
              const Icon = m.icon;
              return (
                <button key={m.key} className={mode === m.key ? "active" : ""} onClick={() => setMode(m.key)}>
                  <Icon size={14} strokeWidth={1.8} />{m.label}
                </button>
              );
            })}
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
            <div className="globe-canvas-wrap dark-panel">
              <Globe3D points={points} height={460} onPointClick={(pt) => {
                const c = structures.candidates.find((cand) => cand.candidate_id === pt.id);
                if (c) openInspector("candidate", c);
              }} />
              <p className="globe-caption small">
                Gold = strongest priced structure · jade = another priced option · amber = requires an authority
                decision before it can be priced · silver = viable but not yet priced. Treaty routes aren't shown —
                none of today's candidates use a treaty structure.
              </p>
            </div>
          )}

          {mode === "split" && (
            <div className="split-workspace">
              <div className="split-lane-row">
                {structures.candidates.map((c) => {
                  const rankIndex = structures.ranking.findIndex((r) => r.structure_id === c.candidate_id);
                  const tier = candidateTier(c, rankIndex);
                  return (
                    <div key={c.candidate_id} className={`split-lane-mini lane-${tier}`} onClick={() => openInspector("candidate", c)}>
                      <div className="row-title" style={{ fontSize: 12 }}>{structureLabel(c.participating_jurisdictions)}</div>
                      <div className="row-sub"><Pct value={c.priceable_pct} /> priceable</div>
                    </div>
                  );
                })}
              </div>
              <div className="globe-canvas-wrap dark-panel">
                <Globe3D points={points} height={340} onPointClick={(pt) => {
                  const c = structures.candidates.find((cand) => cand.candidate_id === pt.id);
                  if (c) openInspector("candidate", c);
                }} />
              </div>
            </div>
          )}
        </div>

        <aside className="workspace-side">
          <div className="workspace-side-tabs">
            <button className={sideTab === "questions" ? "active" : ""} onClick={() => setSideTab("questions")}>
              Questions <span className="text-tertiary">{pkg.missing_inputs.length + legal.grey_areas_current.filter((g) => g.status === "open").length}</span>
            </button>
            <button className={sideTab === "recommendations" ? "active" : ""} onClick={() => setSideTab("recommendations")}>
              Recommendations
            </button>
          </div>
          <div className="workspace-side-body">
            {sideTab === "questions" ? (
              <>
                <QuestionStack missingInputs={pkg.missing_inputs} greyAreas={legal.grey_areas_current} />
                <div className="trace-trigger-row">
                  {legal.grey_areas_current.map((g) => (
                    <button key={g.item_id} className={`tag ${activeGreyArea?.item_id === g.item_id ? "active" : ""}`} onClick={() => setActiveGreyArea(g)}>
                      Trace {g.jurisdiction_code} · <Money value={g.amount_usd} /> <ChevronDown size={12} />
                    </button>
                  ))}
                </div>
                {activeGreyArea && <EconomicsTrace greyArea={activeGreyArea} legal={legal} />}
              </>
            ) : (
              <RecommendationsList byCategory={recommendations.by_category} legal={recommendations.legal} />
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
