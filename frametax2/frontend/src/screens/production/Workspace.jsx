import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, humanizeToken, programDisplay } from "../../lib/format";
import { useAppState } from "../../state/AppState";
import Globe3D from "../../components/Globe3D";
import { buildGlobeData, structureTier } from "../../lib/globeData";
import QuestionStack from "../../components/QuestionStack";
import RecommendationsList from "../../components/RecommendationsList";
import EconomicsTrace from "../../components/EconomicsTrace";
import QualificationPanel from "../../components/QualificationPanel";
import { InspectorBody } from "../../shell/Inspector";

// Docked-inspector header label per selection kind (frozen artifact
// "Selection · Question" convention).
const INSPECT_KIND_LABEL = {
  question: "Question",
  "allocation-segment": "Segment",
  "allocation-assignment": "Routing",
  "structure-recommendation": "Structure",
  recommendation: "Recommendation",
  candidate: "Candidate",
  jurisdiction: "Jurisdiction",
  account: "Account",
};

// Workspace — the approved artifact "rack" layout
// (reference/artifacts/prototype-v1-updated.html): a collapsible question
// stack on the left, a full-width grid of universal scenario cards in the
// centre (or the Map/Split globe), and a two-group leading-structure strip
// pinned to the bottom. The right-hand Inspector is the app-level overlay
// (openInspector). Every card value is read verbatim from the allocated
// structure — Qualified spend is the backend's own per-segment QPE summed;
// Gross incentive is total_incentive_floor_usd; NPC is
// npc_with_adjustments_usd. No client-side derivation.

const MODES = [
  { key: "lanes", label: "Lanes" },
  { key: "map", label: "Map" },
  { key: "split", label: "Split" },
];
const CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧"];
const pct = (part, whole) => (whole ? Math.max(0, Math.min(100, (part / whole) * 100)) : 0);
// Display currency per jurisdiction, limited to what /economics.fx_horizons serves.
const FX_CCY = { MU: "MUR", MT: "EUR", IE: "EUR", GR: "EUR", GB: "GBP", IT: "EUR", ES: "EUR", FR: "EUR", DE: "EUR" };

function ScenarioCard({ structure, tier, rank, grossBudget, isLeading, fxHorizons, onSetLeading, onInspect, onCompare, onSelectSegment }) {
  const priced = structure.is_fully_priced;
  const qualifiedSpend = structure.segments?.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0) || 0;
  const npc = structure.npc_with_adjustments_usd;

  const laneClass = isLeading ? "anchor" : priced ? "" : "draft";
  const badge = isLeading ? "① LEADING" : priced ? (CIRCLED[(rank?.rank || 1) - 1] || `#${rank?.rank}`) : "DRAFT";

  // Per-lane FX chip — real spot for the structure's dominant jurisdiction
  // currency (frozen-artifact .lane-fx presentation, honest backend data).
  const dominant = structure.segments?.slice().sort((a, b) => (b.qpe_usd || 0) - (a.qpe_usd || 0))[0];
  const fxCcy = FX_CCY[dominant?.jurisdiction_code];
  const fxSpot = fxCcy ? fxHorizons?.[fxCcy]?.current : null;

  return (
    <div className={`wsx-lane ${laneClass}`}>
      <div className="wsx-lh">
        <div className="wsx-lh-id">
          <div className="wsx-nm">{structure.label}</div>
          {/* Sub-line — the artifact's "program · rate" contract for priced
              lanes, from the dominant segment's REAL program + floor rate;
              drafts keep the canonical structure-type description. */}
          <div className="wsx-lb">
            {priced && dominant?.claims_incentive && dominant?.program_slug
              ? `${programDisplay(dominant.program_slug)} · ${Math.round((dominant.rate_floor || 0) * 100)}%${dominant.is_band_ceiling ? " (up to)" : ""}`
              : `${humanizeToken(structure.structure_type)}${structure.participants?.length ? ` · ${structure.participants.join(" · ")}` : ""}`}
          </div>
          {fxSpot != null && (
            <div className="wsx-lane-fx" onClick={() => onInspect(structure)} title={`USD/${fxCcy} · live spot`}>
              <span className="fx-pair">USD/{fxCcy}</span>
              <span className="fx-note">{Number(fxSpot).toFixed(2)} · live spot</span>
            </div>
          )}
        </div>
        <span className="wsx-badge">{badge}</span>
      </div>

      {priced ? (
        <>
          <div className="wsx-rows">
            <div className="wsx-row"><span>Gross budget</span><span><Money value={grossBudget} bare /></span></div>
            <div className="wsx-row"><span>Qualified spend</span><span><Money value={qualifiedSpend} bare /></span></div>
            <div className="wsx-row"><span>Gross incentive</span><span className="incentive"><Money value={structure.total_incentive_floor_usd} bare /></span></div>
          </div>
          <div className="wsx-row net"><span>Net production cost</span><span><Money value={npc} bare /></span></div>
          <div className="wsx-range">
            <u style={{ left: 0, width: `${pct(qualifiedSpend, grossBudget)}%` }} />
            <i style={{ left: `${pct(qualifiedSpend, grossBudget)}%`, right: 0 }} />
            <b style={{ left: `${pct(npc, grossBudget)}%` }} />
          </div>
        </>
      ) : (
        <div className="wsx-partial">
          <div className="note">Not yet priced — {structure.blockers.length} blocker{structure.blockers.length === 1 ? "" : "s"}.</div>
          {structure.blockers.slice(0, 3).map((b, i) => <p key={i}>{b}</p>)}
          {structure.blockers.length > 3 && <p>+{structure.blockers.length - 3} more — open the recommendation for the full trace.</p>}
        </div>
      )}

      <div className="wsx-foot">
        <button onClick={() => onInspect(structure)}>Inspect</button>
        <button onClick={() => onCompare(structure)}>Compare</button>
      </div>
      <div className="wsx-lead-act">
        {isLeading ? (
          <button className="wsx-lead is-leading" disabled>● Current leading structure</button>
        ) : (
          <button className="wsx-lead" onClick={() => onSetLeading(structure.structure_id)}>◈ Set as leading</button>
        )}
      </div>
    </div>
  );
}

// Globe chrome — the frozen artifact's overlay panels (info HUD, Layers,
// legend) over the project globe, shown in Map and Split. Counts and legend
// entries describe only what this globe actually renders (live structures,
// treaty arcs, tier colors); layer rows the engine doesn't support yet are
// ghosted exactly like the artifact's own pending rows.
function GlobeChrome({ productionName, nScenarios, nArcs }) {
  return (
    <>
      <div className="wsx-g-hud">
        <b>Project globe · {productionName}</b>
        {nScenarios} scenario{nScenarios === 1 ? "" : "s"} · {nArcs} treaty path{nArcs === 1 ? "" : "s"}
      </div>
      <div className="wsx-g-layers">
        <b>Layers</b>
        <label className="on"><span className="sw2" />Production markers</label>
        <label className="on"><span className="sw2" />Treaty arcs</label>
        <label className="ghosted" title="MapLibre engine"><span className="sw2" />Jurisdiction overlays</label>
        <label className="ghosted" title="MapLibre engine"><span className="sw2" />Country borders</label>
        <label className="ghosted" title="Engine pending"><span className="sw2" />Incentive heat map</label>
        <label className="ghosted" title="Engine pending"><span className="sw2" />Confidence halos</label>
        <label className="ghosted" title="Engine pending"><span className="sw2" />Grey-area halos</label>
        <label className="ghosted" title="Engine pending"><span className="sw2" />Clusters</label>
        <div className="note">Three.js / three-globe — the same rendering engine used by the production terminal.</div>
      </div>
      <div className="wsx-g-legend">
        <span>◉ gold = top-ranked priced</span>
        <span>◉ jade = fully priced</span>
        <span>◉ amber = allocated · blocked</span>
        <span>◉ silver = allocated</span>
        <span>┄ treaty path</span>
      </div>
    </>
  );
}

export default function Workspace() {
  const { data, error, loading, refetch } = useCineGlobe();
  const location = useLocation();
  const navTab = location.state?.tab;

  const [mode, setMode] = useState(navTab === "map" || navTab === "split" ? navTab : "lanes");
  const [qOpen, setQOpen] = useState(navTab === "inputs" || navTab === "recommendations");
  const [qTab, setQTab] = useState(navTab === "inputs" || navTab === "recommendations" ? navTab : "questions");
  const [activeGreyArea, setActiveGreyArea] = useState(null);
  const [leadingOverride, setLeadingOverride] = useState(null);
  const [sortByMoney, setSortByMoney] = useState(true); // artifact "by $ ▾"
  const { openInspector, inspector, closeInspector, setDocked } = useAppState();

  // Dock the Inspector into the Workspace right column (frozen-artifact
  // interaction) for as long as this screen is mounted; the app-level
  // floating overlay stands down meanwhile.
  useEffect(() => {
    setDocked(true);
    return () => setDocked(false);
  }, [setDocked]);

  // Honor cross-page navigation intent (Overview "Deal facts → edit",
  // "Project globe") once the location changes.
  useEffect(() => {
    if (navTab === "map" || navTab === "split") setMode(navTab);
    if (navTab === "inputs" || navTab === "recommendations") { setQOpen(true); setQTab(navTab); }
  }, [navTab]);

  const allocated = data?.structures?.allocated_structures;
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, structuresByCode } = useMemo(
    () => buildGlobeData(allocated, rankById),
    [allocated, rankById],
  );

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, recommendations, legal } = data;
  const openGrey = (legal.grey_areas_current || []).filter((g) => g.status === "open");
  const openCount = (pkg.missing_inputs?.length || 0) + openGrey.length;
  const best = allocated.ranking.find((r) => r.rank === 1);
  const leadingId = leadingOverride ?? best?.structure_id ?? null;
  const leadingStructure = allocated.structures.find((s) => s.structure_id === leadingId);

  // Collapsed-rail status dots — hot for any money-bearing / blocking item.
  const dots = [
    ...openGrey.map(() => "hot"),
    ...(pkg.missing_inputs || []).map((m) => (m.blocking ? "hot" : "")),
  ].slice(0, 8);

  function handleGlobeClick(pt) {
    const s = (structuresByCode.get(pt.id) || [])[0];
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
    <div className="wsx-screen">
      {/* Grid geometry matches the artifact: 48px | 1fr | 38px collapsed;
          left widens to 220px (stack) / 340px (Recs/Inputs); the right
          column widens from the 38px quiet rail to the 300px docked
          Inspector when something is selected (frozen-artifact layoutWork). */}
      <div
        className="wsx-work"
        style={{
          gridTemplateColumns: `${!qOpen ? "48px" : qTab !== "questions" ? "340px" : "220px"} 1fr ${inspector ? "290px" : "38px"}`,
        }}
      >
        {/* Question stack — collapsible left rail. Collapsed by default per
            the artifact; expands into the full work stack (Questions /
            Recommendations / Inputs) so every backend-wired panel stays
            reachable (QualificationPanel = the real POST /people, /facts). */}
        {qOpen ? (
          <aside className="wsx-qstack wsx-qstack-open">
            <div className="wsx-qh">
              Question Stack · {openCount}
              <button className="wsx-qsort" onClick={() => setSortByMoney((v) => !v)} title="Toggle question ordering">
                {sortByMoney ? "by $ ▾" : "by stack ▾"}
              </button>
              <button className="wsx-qcollapse" onClick={() => setQOpen(false)} aria-label="Collapse question stack">⟨</button>
            </div>
            <div className="wsx-qtabs">
              <button className={qTab === "questions" ? "active" : ""} onClick={() => setQTab("questions")}>Questions</button>
              <button className={qTab === "recommendations" ? "active" : ""} onClick={() => setQTab("recommendations")}>Recs</button>
              <button className={qTab === "inputs" ? "active" : ""} onClick={() => setQTab("inputs")}>Inputs</button>
            </div>
            {qTab === "questions" && (
              <>
                <QuestionStack missingInputs={pkg.missing_inputs} greyAreas={legal.grey_areas_current} sortByMoney={sortByMoney} />
                {openGrey.length > 0 && (
                  <div className="trace-trigger-row">
                    {openGrey.map((g) => (
                      <button key={g.item_id} className={`tag ${activeGreyArea?.item_id === g.item_id ? "active" : ""}`} onClick={() => setActiveGreyArea(g)}>
                        Trace {g.jurisdiction_code} · <Money value={g.amount_usd} /> <ChevronDown size={12} />
                      </button>
                    ))}
                  </div>
                )}
                {activeGreyArea && <EconomicsTrace greyArea={activeGreyArea} legal={legal} />}
              </>
            )}
            {qTab === "recommendations" && (
              <RecommendationsList byCategory={recommendations.by_category} legal={recommendations.legal} />
            )}
            {qTab === "inputs" && (
              <QualificationPanel people={data.people} facts={data.facts} script={pkg.script} refetch={refetch} />
            )}
          </aside>
        ) : (
          <aside className="wsx-qstack collapsed">
            <button className="wsx-qexpand" onClick={() => setQOpen(true)} aria-label="Expand question stack">⟩</button>
            <div className="wsx-qcount">{openCount}</div>
            <div className="wsx-qdots">
              {dots.map((d, i) => <i key={i} className={`wsx-qdot ${d}`} />)}
            </div>
          </aside>
        )}

        {/* Station — card rack or globe */}
        <div className="wsx-station">
          <div className="wsx-station-head">
            <div className="wsx-viewtabs">
              {MODES.map((m) => (
                <button key={m.key} className={mode === m.key ? "active" : ""} onClick={() => setMode(m.key)}>
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {mode === "lanes" && (
            <div className="wsx-rack">
              {allocated.structures.map((s) => (
                <ScenarioCard
                  key={s.structure_id}
                  structure={s}
                  tier={structureTier(s, rankById)}
                  rank={rankById.get(s.structure_id)}
                  grossBudget={production.gross_budget_usd}
                  isLeading={s.structure_id === leadingId}
                  fxHorizons={data.economics?.fx_horizons}
                  onSetLeading={setLeadingOverride}
                  onInspect={handleSelectStructure}
                  onCompare={() => { setQOpen(true); setQTab("recommendations"); }}
                  onSelectSegment={handleSelectSegment}
                />
              ))}
              <div className="wsx-lane new" onClick={() => setMode("map")} role="button" title="Add a jurisdiction from the globe">
                <span>+</span>
              </div>
            </div>
          )}

          {mode === "map" && (
            <div className="wsx-globe dark-panel wsx-globe-chrome">
              <Globe3D points={points} arcs={arcs} height={460} onPointClick={handleGlobeClick} />
              <GlobeChrome productionName={production.production_name} nScenarios={allocated.structures.length} nArcs={arcs.length} />
            </div>
          )}

          {mode === "split" && (
            <div className="wsx-splitv">
              <div className="lcol">
                <div className="wsx-rack">
                  {allocated.structures.map((s) => (
                    <ScenarioCard
                      key={s.structure_id}
                      structure={s}
                      tier={structureTier(s, rankById)}
                      rank={rankById.get(s.structure_id)}
                      grossBudget={production.gross_budget_usd}
                      isLeading={s.structure_id === leadingId}
                      fxHorizons={data.economics?.fx_horizons}
                      onSetLeading={setLeadingOverride}
                      onInspect={handleSelectStructure}
                      onCompare={() => { setQOpen(true); setQTab("recommendations"); }}
                      onSelectSegment={handleSelectSegment}
                    />
                  ))}
                </div>
              </div>
              <div className="mcol">
                <div className="wsx-globe dark-panel wsx-globe-chrome">
                  <Globe3D points={points} arcs={arcs} height={480} onPointClick={handleGlobeClick} />
                  <GlobeChrome productionName={production.production_name} nScenarios={allocated.structures.length} nArcs={arcs.length} />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Inspector — docked into the right column per the frozen artifact.
            Populated on selection (question / lane / segment / structure)
            from the shared openInspector state; quiet 38px rail otherwise.
            Same InspectorBody the overlay uses — no forked render, no
            duplicated data. */}
        {inspector ? (
          <aside className="wsx-insp">
            <div className="wsx-insp-inner">
              <div className="wsx-insp-h">
                <span className="kind">Selection · {INSPECT_KIND_LABEL[inspector.kind] || "Detail"}</span>
                <button className="close" onClick={closeInspector} aria-label="Close inspector">✕</button>
              </div>
              <InspectorBody inspector={inspector} />
            </div>
          </aside>
        ) : (
          <div className="wsx-insp-gutter" aria-hidden="true" />
        )}
      </div>

      {/* Leading-structure status strip */}
      <footer className="wsx-status">
        <div className="wsx-st-left">
          <span className="wsx-st-k">Leading structure</span>
          <b>{leadingStructure?.label || "None fully priced yet"}</b>
          {leadingStructure && (() => {
            const seg = leadingStructure.segments?.slice().sort((a, b) => (b.qpe_usd || 0) - (a.qpe_usd || 0))[0];
            return (
              <span className="wsx-st-sub">
                {seg?.claims_incentive && seg?.program_slug
                  ? `${programDisplay(seg.program_slug)} · ${Math.round((seg.rate_floor || 0) * 100)}%`
                  : humanizeToken(leadingStructure.structure_type)}
              </span>
            );
          })()}
        </div>
        <div className="wsx-st-right">
          <span className="lbl">Net production cost</span>
          <span className="mono">{leadingStructure?.is_fully_priced ? <Money value={leadingStructure.npc_with_adjustments_usd} /> : "—"}</span>
          <span className="meta">{openCount} question{openCount === 1 ? "" : "s"} open</span>
        </div>
      </footer>
    </div>
  );
}
