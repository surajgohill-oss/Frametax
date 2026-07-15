import { useMemo, useState } from "react";
import { Rows3, Globe2, Columns2, ChevronDown } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, accountStateLabel, humanizeToken } from "../../lib/format";
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

const TIER_RANK = { gold: 4, jade: 3, amber: 2, silver: 1 };

// Tier is derived entirely from the allocated structure's own real
// fields (allocated_structures.ranking + is_fully_priced + blockers) —
// never a client-side re-derivation of pricing.
function structureTier(structure, rankById) {
  const rank = rankById.get(structure.structure_id);
  if (rank?.rank === 1) return "gold";
  if (structure.is_fully_priced) return "jade";
  if (structure.blockers?.length > 0) return "amber";
  return "silver";
}

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

function AllocatedLane({ structure, tier, rank, onSelectStructure, onSelectSegment }) {
  return (
    <div className={`lane lane-${tier}`} onClick={() => onSelectStructure(structure)}>
      <div className="lane-header">
        <span className="lane-title">{structure.label}</span>
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
          <div className="lane-metric-row"><span className="label">Incentive (floor)</span><span className="mono"><Money value={structure.total_incentive_floor_usd} /></span></div>
          <div className="lane-metric-row"><span className="label">Net production cost (verified)</span><span className="mono"><Money value={structure.npc_verified_usd} /></span></div>
          <div className="lane-metric-row"><span className="label">Net production cost (with adjustments)</span><span className="mono"><Money value={structure.npc_with_adjustments_usd} /></span></div>
          {structure.financing_cost_usd > 0 && (
            <div className="lane-metric-row"><span className="label">Financing cost</span><span className="mono"><Money value={structure.financing_cost_usd} /></span></div>
          )}
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
    </div>
  );
}

export default function Workspace() {
  const { data, error, loading } = useCineGlobe();
  const [mode, setMode] = useState("lanes");
  const [sideTab, setSideTab] = useState("questions");
  const [activeGreyArea, setActiveGreyArea] = useState(null);
  const { openInspector } = useAppState();

  const allocated = data?.structures?.allocated_structures;

  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);

  // Builds the globe's points/arcs from the SAME allocated_structures
  // payload the Lane Rack renders — one live production model, never two
  // divergent data sources feeding LANES vs MAP/SPLIT. structuresByCode
  // (best-tier-first per jurisdiction) also drives globe click → Inspector.
  const { points, arcs, structuresByCode } = useMemo(() => {
    if (!allocated) return { points: [], arcs: [], structuresByCode: new Map() };
    const tierByCode = new Map();
    const byCode = new Map();
    const arcList = [];
    for (const s of allocated.structures) {
      const tier = structureTier(s, rankById);
      for (const code of s.participants) {
        if (!JURISDICTION_COORDS[code]) continue;
        const list = byCode.get(code) || [];
        list.push(s);
        byCode.set(code, list);
        const existingTier = tierByCode.get(code);
        if (!existingTier || TIER_RANK[tier] > TIER_RANK[existingTier]) tierByCode.set(code, tier);
      }
      if (s.treaty_slug && s.participants.length === 2) {
        const [a, b] = s.participants;
        const ca = JURISDICTION_COORDS[a];
        const cb = JURISDICTION_COORDS[b];
        if (ca && cb) arcList.push({ startLat: ca.lat, startLng: ca.lng, endLat: cb.lat, endLng: cb.lng, tier });
      }
    }
    for (const list of byCode.values()) {
      list.sort((x, y) => TIER_RANK[structureTier(y, rankById)] - TIER_RANK[structureTier(x, rankById)]);
    }
    const pointList = [...tierByCode.entries()].map(([code, tier]) => ({
      lat: JURISDICTION_COORDS[code].lat, lng: JURISDICTION_COORDS[code].lng, tier, name: code, id: code,
    }));
    return { points: pointList, arcs: arcList, structuresByCode: byCode };
  }, [allocated, rankById]);

  const budgetBlocks = useMemo(() => (data ? buildAccountBlocks(data.pkg.register) : []), [data]);
  const maxBlockAmount = useMemo(() => Math.max(1, ...budgetBlocks.map((b) => b.amount)), [budgetBlocks]);

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, recommendations, legal } = data;
  const best = allocated.ranking.find((r) => r.rank === 1);

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
      <div className="workspace-verdict">
        <span className={`dot ${best ? "gold" : "silver"}`} />
        <span>Best current structure: <strong>{best?.label || "None fully priced yet"}</strong></span>
        {best && (
          <>
            <span className="text-tertiary">·</span>
            <span className="mono"><Money value={best.npc_with_adjustments_usd} /> net production cost (incentive, travel and FX applied)</span>
          </>
        )}
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
                <AllocatedLane
                  key={s.structure_id}
                  structure={s}
                  tier={structureTier(s, rankById)}
                  rank={rankById.get(s.structure_id)}
                  onSelectStructure={handleSelectStructure}
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
