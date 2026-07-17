import { useMemo, useState } from "react";
import { Rows3, Globe2, Columns2, ChevronDown } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, accountStateLabel, humanizeToken } from "../../lib/format";
import { buildAccountBlocks } from "../../lib/budgetBlocks";
import { useAppState } from "../../state/AppState";
import Globe3D from "../../components/Globe3D";
import { buildGlobeData, structureTier } from "../../lib/globeData";
import QuestionStack from "../../components/QuestionStack";
import RecommendationsList from "../../components/RecommendationsList";
import EconomicsTrace from "../../components/EconomicsTrace";
import QualificationPanel from "../../components/QualificationPanel";

const MODES = [
  { key: "lanes", label: "Lanes", icon: Rows3 },
  { key: "map", label: "Map", icon: Globe2 },
  { key: "split", label: "Split", icon: Columns2 },
];

// Cross-references one budget account against every allocated structure's
// own segments — "jurisdiction comparison" / "affected structures" for
// the Model Rail expanded view. Every field is read verbatim from
// allocated_structures; a segment's blockers are its own explanation.
function computeAccountCrossRef(code, allocated) {
  if (!allocated) return [];
  return allocated.structures
    .map((s) => {
      const seg = s.segments.find((sg) => sg.account_codes.includes(code));
      if (!seg) return null;
      return {
        structureId: s.structure_id,
        structureLabel: s.label,
        jurisdictionCode: seg.jurisdiction_code,
        claimsIncentive: seg.claims_incentive,
        qpeUsd: seg.qpe_usd,
        incentiveFloorUsd: seg.incentive_floor_usd,
        blockers: seg.blockers,
      };
    })
    .filter(Boolean);
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

// Approved universal scenario card: identical internal structure on every
// card — Gross Budget / Qualified Spend / Gross Incentive / dominant NPC,
// then Inspect + Compare, then the leading-structure control. Every value
// is read verbatim from the allocated structure (qualified spend = the
// backend's own per-segment QPE, summed; incentive = total_incentive_floor_usd;
// NPC = npc_with_adjustments_usd). No Net Benefit, no Timing.
function ScenarioCard({ structure, tier, rank, grossBudget, isLeading, onSetLeading, onInspect, onCompare, onSelectSegment }) {
  const qualifiedSpend = structure.segments?.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0);
  return (
    <div className={`lane lane-${tier}`}>
      <div className="lane-header">
        <span className="lane-title serif card-title">{structure.label}</span>
        <span className={`dot ${tier}`} />
      </div>
      <p className="lane-sub text-tertiary small">
        {humanizeToken(structure.structure_type)}{rank?.rank ? ` · rank ${rank.rank}` : ""}
      </p>

      <div className="tag-row" style={{ marginTop: 6 }}>
        {structure.participants.map((code) => (
          <button
            key={code}
            className="tag"
            onClick={(e) => { e.stopPropagation(); onSelectSegment(structure, code); }}
          >
            {code}
          </button>
        ))}
      </div>

      {structure.is_fully_priced ? (
        <>
          <div className="card-rows">
            <div className="card-row"><span className="label">Gross budget</span><span className="mono"><Money value={grossBudget} /></span></div>
            <div className="card-row"><span className="label">Qualified spend</span><span className="mono"><Money value={qualifiedSpend} /></span></div>
            <div className="card-row"><span className="label">Gross incentive</span><span className="mono card-incentive"><Money value={structure.total_incentive_floor_usd} /></span></div>
          </div>
          <div className="card-npc">
            <span className="card-npc-label">Net production cost</span>
            <span className="mono card-npc-value"><Money value={structure.npc_with_adjustments_usd} /></span>
          </div>
        </>
      ) : (
        <div style={{ marginTop: 8 }}>
          <p className="lane-partial-note">
            Not yet priced — {structure.blockers.length} blocker{structure.blockers.length === 1 ? "" : "s"}.
          </p>
          {structure.blockers.slice(0, 3).map((b, i) => (
            <p key={i} className="text-tertiary small" style={{ margin: "4px 0" }}>{b}</p>
          ))}
          {structure.blockers.length > 3 && (
            <p className="text-tertiary small">+{structure.blockers.length - 3} more blocker(s) — open the recommendation for the full trace.</p>
          )}
        </div>
      )}

      <div className="card-actions">
        <button className="card-action" onClick={(e) => { e.stopPropagation(); onInspect(structure); }}>Inspect</button>
        <button className="card-action" onClick={(e) => { e.stopPropagation(); onCompare(structure); }}>Compare</button>
      </div>
      <div className="card-lead-row">
        {isLeading ? (
          <button className="card-lead is-leading" disabled>● Current leading structure</button>
        ) : (
          <button className="card-lead" onClick={(e) => { e.stopPropagation(); onSetLeading(structure.structure_id); }}>◈ Set as leading</button>
        )}
      </div>
    </div>
  );
}

export default function Workspace() {
  const { data, error, loading, refetch } = useCineGlobe();
  const [mode, setMode] = useState("lanes");
  const [sideTab, setSideTab] = useState("questions");
  const [activeGreyArea, setActiveGreyArea] = useState(null);
  // Presentation-only leading-structure choice (approved "Set as Leading"
  // control). Defaults to the backend's own rank-1 structure; no backend
  // persistence or re-ranking is wired in this pass.
  const [leadingOverride, setLeadingOverride] = useState(null);
  const { openInspector } = useAppState();

  const allocated = data?.structures?.allocated_structures;

  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);

  // One live production model feeding LANES and MAP/SPLIT alike — shared
  // with Overview via lib/globeData.
  const { points, arcs, structuresByCode } = useMemo(
    () => buildGlobeData(allocated, rankById),
    [allocated, rankById],
  );

  const budgetBlocks = useMemo(() => (data ? buildAccountBlocks(data.pkg.register) : []), [data]);
  const maxBlockAmount = useMemo(() => Math.max(1, ...budgetBlocks.map((b) => b.amount)), [budgetBlocks]);

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, recommendations, legal } = data;
  const best = allocated.ranking.find((r) => r.rank === 1);
  // Effective leading structure: presentation override if set, otherwise
  // the backend's own rank-1 result.
  const leadingId = leadingOverride ?? best?.structure_id ?? null;
  const leadingStructure = allocated.structures.find((s) => s.structure_id === leadingId);

  function handleGlobeClick(pt) {
    const list = structuresByCode.get(pt.id) || [];
    const s = list[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === pt.id);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }

  function handleSelectStructure(structure) {
    if (structure.recommendation) openInspector("structure-recommendation", structure.recommendation);
    else if (structure.segments?.[0]) openInspector("allocation-segment", { ...structure.segments[0], structureLabel: structure.label });
  }

  function handleSelectSegment(structure, code) {
    const seg = structure.segments.find((sg) => sg.jurisdiction_code === code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: structure.label });
  }

  return (
    <div className="workspace-screen">
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
              onSelectAccount={(line) => openInspector("account", { ...line, crossRef: computeAccountCrossRef(line.code, allocated) })}
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
              {allocated.structures.map((s) => (
                <ScenarioCard
                  key={s.structure_id}
                  structure={s}
                  tier={structureTier(s, rankById)}
                  rank={rankById.get(s.structure_id)}
                  grossBudget={production.gross_budget_usd}
                  isLeading={s.structure_id === leadingId}
                  onSetLeading={setLeadingOverride}
                  onInspect={handleSelectStructure}
                  onCompare={() => setSideTab("recommendations")}
                  onSelectSegment={handleSelectSegment}
                />
              ))}
            </div>
          )}

          {mode === "map" && (
            <div className="globe-canvas-wrap dark-panel">
              <Globe3D points={points} arcs={arcs} height={460} onPointClick={handleGlobeClick} />
              <p className="globe-caption small">
                Gold = top-ranked fully priced structure · jade = another fully priced structure · amber = allocated
                but blocked by an unresolved requirement · silver = allocated, not the top-priced route.
                {arcs.length > 0
                  ? " Dashed arcs mark treaty co-production routes."
                  : ` No treaty co-production structure is currently priced — see coverage.reachable_treaty_partners (${allocated.coverage.reachable_treaty_partners.length}) in Knowledge.`}
              </p>
            </div>
          )}

          {mode === "split" && (
            <div className="split-workspace">
              <div className="split-lane-row">
                {allocated.structures.map((s) => {
                  const tier = structureTier(s, rankById);
                  return (
                    <div key={s.structure_id} className={`split-lane-mini lane-${tier}`} onClick={() => handleSelectStructure(s)}>
                      <div className="row-title" style={{ fontSize: 12 }}>{s.label}</div>
                      <div className="row-sub">
                        {s.is_fully_priced ? "Fully priced" : `${s.blockers.length} blocker${s.blockers.length === 1 ? "" : "s"}`}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="globe-canvas-wrap dark-panel">
                <Globe3D points={points} arcs={arcs} height={340} onPointClick={handleGlobeClick} />
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
            <button className={sideTab === "inputs" ? "active" : ""} onClick={() => setSideTab("inputs")}>
              Inputs
            </button>
          </div>
          <div className="workspace-side-body">
            {sideTab === "questions" && (
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
            )}
            {sideTab === "recommendations" && (
              <RecommendationsList byCategory={recommendations.by_category} legal={recommendations.legal} />
            )}
            {sideTab === "inputs" && (
              /* Optimizer inputs — treaty eligibility, cultural qualification,
                 allocation assumptions. Real POST /people + POST /facts wiring,
                 relocated from Overview per the approved architecture (these
                 belong in Workspace, not Overview). */
              <QualificationPanel people={data.people} facts={data.facts} script={pkg.script} refetch={refetch} />
            )}
          </div>
        </aside>
      </div>

      {/* Leading-structure rail — two aligned typographic groups, not one
          flat sentence. Left: eyebrow / structure. Right: NPC. */}
      <footer className="leading-rail">
        <div className="lr-left">
          <span className="lr-eyebrow">Leading structure</span>
          <span className="serif lr-name">{leadingStructure?.label || "None fully priced yet"}</span>
          {leadingStructure && (
            <span className="lr-sub text-tertiary small">{humanizeToken(leadingStructure.structure_type)}</span>
          )}
        </div>
        <div className="lr-right">
          <span className="lr-label">Net production cost</span>
          <span className="mono lr-value">
            {leadingStructure?.is_fully_priced
              ? <Money value={leadingStructure.npc_with_adjustments_usd} />
              : "—"}
          </span>
        </div>
      </footer>
    </div>
  );
}
