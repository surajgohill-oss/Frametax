import { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import { Money, scenarioDisplay, confidenceStatusLabel, confidenceStatusTone } from "../../lib/format";
import { useAppState } from "../../state/AppState";
import Globe3D from "../../components/Globe3D";
import { buildGlobeView, structureTier, activeStructure } from "../../lib/globeData";
import GlobeLegend from "../../components/GlobeLegend";
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
// Gross incentive is selected_incentive_usd (best-supported modeled rate);
// NPC is npc_with_adjustments_usd (modeled + normalizations). No client-side
// derivation.

const MODES = [
  { key: "lanes", label: "Lanes" },
  { key: "map", label: "Map" },
  { key: "split", label: "Split" },
];
const CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧"];

// The optimizer may compose far more structures than a card rack can
// usefully show at once (every discovery-retained partner — incentive-
// ready AND capability-only — gets a full-relocation and a component
// candidate). Six visible cards, swap-in overflow — the same contract
// Scenarios.jsx uses, over the SAME ordering rule (rank-first, then
// composition order), so both screens show the same six by default
// without needing shared mutable state.
const MAX_VISIBLE = 6;
function visibleStructures(structures, rankById, swapId) {
  const ordered = [...structures].sort((a, b) => {
    const ra = rankById.get(a.structure_id)?.rank ?? Infinity;
    const rb = rankById.get(b.structure_id)?.rank ?? Infinity;
    return ra - rb;
  });
  const base = ordered.slice(0, MAX_VISIBLE);
  const overflow = ordered.slice(MAX_VISIBLE);
  const swapped = swapId ? ordered.find((s) => s.structure_id === swapId) : null;
  const cols = swapped ? [...base.slice(0, MAX_VISIBLE - 1), swapped] : base;
  return { base, overflow, cols };
}
const pct = (part, whole) => (whole ? Math.max(0, Math.min(100, (part / whole) * 100)) : 0);

function ScenarioCard({ structure, tier, rank, grossBudget, budgetReconciliation, isLeading, onSetLeading, onInspect, onCompare, onSelectSegment }) {
  const priced = structure.is_fully_priced;
  // All four card figures read from THIS scenario's canonical allocated
  // structure — gross from structure.gross_budget_usd (falls back to the
  // production-level prop only if a structure ever omits it), qualified
  // spend from its own per-segment QPE, incentive and NPC from its own
  // priced fields. No production-level or prototype figure is shown.
  const gross = structure.gross_budget_usd ?? grossBudget;
  const qualifiedSpend = structure.segments?.reduce((sum, sg) => sum + (sg.qpe_usd || 0), 0) || 0;
  const npc = structure.npc_with_adjustments_usd;
  // Segment QPE is summed from the same 44 real leaf accounts the
  // production's budget_reconciliation already discloses (GET /production).
  // When a structure's own qualification pipeline excludes nothing from
  // any segment, that sum lands on the leaf-account total rather than the
  // source document's stated Grand Total ("Gross budget" above) — a $2
  // source-document rounding variance, not fabricated or double-counted
  // spend and not a statutory uplift. Disclose it inline rather than
  // showing an unexplained "qualified spend > gross budget."
  const overGross = qualifiedSpend > gross;

  const laneClass = isLeading ? "anchor" : priced ? "" : "draft";
  const badge = isLeading ? "① LEADING" : priced ? (CIRCLED[(rank?.rank || 1) - 1] || `#${rank?.rank}`) : "DRAFT";

  // Producer-facing title/subtitle — the ONE canonical formatter
  // (lib/format.jsx scenarioDisplay), shared by Workspace/Overview/
  // Scenarios/Reports.
  const { title, subtitle } = scenarioDisplay(structure);
  // FX presentation is intentionally hidden here for now: structure.fx_basis
  // is real, sourced exchange-rate provenance (currency/rate/source/date),
  // but under the default economics controls fx_delta_usd is always $0 —
  // "priced at spot, no currency stress modeled" — which reads to a
  // producer as a meaningful adjustment when it isn't one yet. The backend
  // still computes and serves it; a real FX adjustment (applied only to
  // currency-exposed local spend) belongs in the Inspector later, not a
  // prominent card chip.

  return (
    <div className={`wsx-lane ${laneClass}`}>
      <div className="wsx-lh">
        <div className="wsx-lh-id">
          <div className="wsx-nm">{title}</div>
          <div className="wsx-lb">{subtitle}</div>
          {structure.confidence_status && (
            <div
              className={`wsx-conf ${confidenceStatusTone(structure.confidence_status)}`}
              title={(structure.confidence_reasons || []).join(" ")}
            >
              {confidenceStatusLabel(structure.confidence_status)}
            </div>
          )}
        </div>
        <span className="wsx-badge">{badge}</span>
      </div>

      {priced ? (
        <>
          <div className="wsx-rows">
            <div className="wsx-row"><span>Gross budget</span><span><Money value={gross} bare /></span></div>
            <div className="wsx-row">
              <span>
                Qualified spend
                {overGross && (
                  <sup
                    className="wsx-recon-flag"
                    title={
                      budgetReconciliation?.note ||
                      "Sums the same real budget accounts the production's Gross budget is drawn from, but on a leaf-account basis rather than the source document's stated Grand Total — a small source-document rounding variance, not additional or double-counted spend."
                    }
                  >
                    †
                  </sup>
                )}
              </span>
              <span><Money value={qualifiedSpend} bare /></span>
            </div>
            <div className="wsx-row"><span>Gross incentive</span><span className="incentive"><Money value={structure.selected_incentive_usd} bare /></span></div>
          </div>
          {overGross && (
            <div className="wsx-recon-note">
              † Qualified spend exceeds gross budget by <Money value={qualifiedSpend - gross} bare /> — a disclosed
              source-document rounding variance between the budget's stated Grand Total and the sum of its own leaf
              accounts, not additional qualifying spend.
            </div>
          )}
          <div className="wsx-row net"><span>Net production cost</span><span><Money value={npc} bare /></span></div>
          <div className="wsx-range">
            <u style={{ left: 0, width: `${pct(qualifiedSpend, gross)}%` }} />
            <i style={{ left: `${pct(qualifiedSpend, gross)}%`, right: 0 }} />
            <b style={{ left: `${pct(npc, gross)}%` }} />
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

// Globe chrome — the two overlays that carry production value: a context
// HUD (which production, how many composed scenarios) and the shared
// status legend. The old "Layers" panel was prototype scaffolding — two
// toggles that controlled nothing plus four permanently-ghosted "engine
// pending" rows and a note naming the rendering library — so it has been
// removed rather than shipped to producers. Country polygon fill and
// borders are the Globe's primary always-on visualization, never a
// togglable layer. The legend is the shared GlobeLegend component so this
// screen cannot drift from Project Globe's wording or colours.
function GlobeChrome({ productionName, nScenarios, nArcs }) {
  return (
    <>
      <div className="wsx-g-hud">
        <b>Project globe · {productionName}</b>
        {nScenarios} scenario{nScenarios === 1 ? "" : "s"} · {nArcs} structure route{nArcs === 1 ? "" : "s"}
      </div>
      <GlobeLegend className="globe-legend-overlay" showTreatyPath={nArcs > 0} />
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
  const [sortByMoney, setSortByMoney] = useState(true); // artifact "by $ ▾"
  const [swapId, setSwapId] = useState("");
  const [globeMode, setGlobeMode] = useState("jurisdictions"); // "jurisdictions" | "optimizer"
  const [globeHover, setGlobeHover] = useState(null);
  const {
    openInspector, inspector, closeInspector, setDocked,
    leadingStructureId, setLeadingStructureId,
    selectedJurisdiction, setSelectedJurisdiction,
  } = useAppState();

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
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode } = useMemo(
    () => buildGlobeView(allocated, rankById, { mode: globeMode, leadingStructureId, selectedJurisdiction }),
    [allocated, rankById, globeMode, leadingStructureId, selectedJurisdiction],
  );

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, recommendations, legal } = data;
  const openGrey = (legal.grey_areas_current || []).filter((g) => g.status === "open");
  const openCount = (pkg.missing_inputs?.length || 0) + openGrey.length;
  const leadingStructure = activeStructure(allocated, leadingStructureId);
  const leadingId = leadingStructure?.structure_id ?? null;
  const { overflow, cols } = visibleStructures(allocated.structures, rankById, swapId);

  // Collapsed-rail status dots — hot for any money-bearing / blocking item.
  const dots = [
    ...openGrey.map(() => "hot"),
    ...(pkg.missing_inputs || []).map((m) => (m.blocking ? "hot" : "")),
  ].slice(0, 8);

  const contingencyByAccount = allocated?.contingency || {};
  function handleGlobeClick(pt) {
    const code = pt.jurisdictionCode || pt.id;
    setSelectedJurisdiction(code);
    const s = (structuresByCode.get(code) || [])[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label, contingencyByAccount });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }
  function handleSelectStructure(structure) {
    if (structure.recommendation) openInspector("structure-recommendation", structure.recommendation);
    else if (structure.segments?.[0]) openInspector("allocation-segment", { ...structure.segments[0], structureLabel: structure.label, contingencyByAccount });
  }
  function handleSelectSegment(structure, code) {
    const seg = structure.segments.find((sg) => sg.jurisdiction_code === code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: structure.label, contingencyByAccount });
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
            {(mode === "map" || mode === "split") && (
              <div className="wsx-viewtabs" title="Jurisdictions: every participating jurisdiction, colored by qualification. Optimizer: only the leading structure's own routing chain.">
                <button className={globeMode === "jurisdictions" ? "active" : ""} onClick={() => setGlobeMode("jurisdictions")}>Jurisdictions</button>
                <button className={globeMode === "optimizer" ? "active" : ""} onClick={() => setGlobeMode("optimizer")}>Optimizer Overlay</button>
              </div>
            )}
            {mode !== "map" && overflow.length > 0 && (
              <div className="wsx-scenario-select">
                <label htmlFor="wsx-swap">Additional scenario</label>
                <select
                  id="wsx-swap"
                  className="field-select"
                  value={swapId}
                  onChange={(e) => setSwapId(e.target.value)}
                >
                  <option value="">— {scenarioDisplay(cols[cols.length - 1] || {}).title} —</option>
                  {overflow.map((s) => (
                    <option key={s.structure_id} value={s.structure_id}>{scenarioDisplay(s).title}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {mode === "lanes" && (
            <div className="wsx-rack">
              {cols.map((s) => (
                <ScenarioCard
                  key={s.structure_id}
                  structure={s}
                  tier={structureTier(s, rankById)}
                  rank={rankById.get(s.structure_id)}
                  grossBudget={production.gross_budget_usd}
                  budgetReconciliation={production.budget_reconciliation}
                  isLeading={s.structure_id === leadingId}
                  onSetLeading={setLeadingStructureId}
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
              <Globe3D
                points={points}
                arcs={arcs}
                height={460}
                pointRadius={0.22}
                polygonColors={polygonColors}
                selectedIso={selectedIso}
                selectedLat={selectedLat}
                selectedLng={selectedLng}
          focusLat={focusLat}
          focusLng={focusLng}
          focusDistance={focusDistance}
                onPointClick={handleGlobeClick}
                onPointHover={setGlobeHover}
              />
              <GlobeChrome productionName={production.production_name} nScenarios={allocated.structures.length} nArcs={arcs.length} />
              {globeHover && (
                <div className="globe-tooltip">
                  <strong>{globeHover.jurisdictionName}</strong>
                  <div className="text-tertiary small">{globeHover.statusLabel}</div>
                  {globeHover.role && <div className="text-tertiary small">{globeHover.role}</div>}
                  {globeHover.incentiveUsd != null && <div className="small">Incentive <Money value={globeHover.incentiveUsd} /></div>}
                  {globeHover.npcUsd != null && <div className="small">NPC <Money value={globeHover.npcUsd} /></div>}
                </div>
              )}
            </div>
          )}

          {mode === "split" && (
            <div className="wsx-splitv">
              <div className="lcol">
                <div className="wsx-rack">
                  {cols.map((s) => (
                    <ScenarioCard
                      key={s.structure_id}
                      structure={s}
                      tier={structureTier(s, rankById)}
                      rank={rankById.get(s.structure_id)}
                      grossBudget={production.gross_budget_usd}
                      budgetReconciliation={production.budget_reconciliation}
                      isLeading={s.structure_id === leadingId}
                      onSetLeading={setLeadingStructureId}
                      onInspect={handleSelectStructure}
                      onCompare={() => { setQOpen(true); setQTab("recommendations"); }}
                      onSelectSegment={handleSelectSegment}
                    />
                  ))}
                </div>
              </div>
              <div className="mcol">
                <div className="wsx-globe dark-panel wsx-globe-chrome">
                  <Globe3D
                    points={points}
                    arcs={arcs}
                    height={480}
                    pointRadius={0.22}
                    polygonColors={polygonColors}
                    selectedIso={selectedIso}
                    selectedLat={selectedLat}
                    selectedLng={selectedLng}
          focusLat={focusLat}
          focusLng={focusLng}
          focusDistance={focusDistance}
                    onPointClick={handleGlobeClick}
                    onPointHover={setGlobeHover}
                  />
                  <GlobeChrome productionName={production.production_name} nScenarios={allocated.structures.length} nArcs={arcs.length} />
                  {globeHover && (
                    <div className="globe-tooltip">
                      <strong>{globeHover.jurisdictionName}</strong>
                      <div className="text-tertiary small">{globeHover.statusLabel}</div>
                      {globeHover.role && <div className="text-tertiary small">{globeHover.role}</div>}
                      {globeHover.incentiveUsd != null && <div className="small">Incentive <Money value={globeHover.incentiveUsd} /></div>}
                      {globeHover.npcUsd != null && <div className="small">NPC <Money value={globeHover.npcUsd} /></div>}
                    </div>
                  )}
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
          <b>{leadingStructure ? scenarioDisplay(leadingStructure).title : "None fully priced yet"}</b>
          {leadingStructure && <span className="wsx-st-sub">{scenarioDisplay(leadingStructure).subtitle}</span>}
          {leadingStructure?.confidence_status && (
            <span
              className={`wsx-conf ${confidenceStatusTone(leadingStructure.confidence_status)}`}
              title={(leadingStructure.confidence_reasons || []).join(" ")}
            >
              {confidenceStatusLabel(leadingStructure.confidence_status)}
            </span>
          )}
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
