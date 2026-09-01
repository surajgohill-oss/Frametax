import { useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { useAppState } from "../../state/AppState";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import GlobeHoverCard from "../../components/GlobeHoverCard";
import { buildGlobeView, activeStructure } from "../../lib/globeData";
import { bestPricedCandidate } from "../../lib/bestPricedCandidate";
import ProductionDetails from "../../components/ProductionDetails";
import BudgetRail from "../../components/BudgetRail";
import IncentiveIntelligence from "../../components/IncentiveIntelligence";
// FXStrip: REMOVED from this Overview position this batch (see Batch 2 —
// the full-width strip demoted the Globe and broke the approved
// hero -> tabs -> three-column composition). FXStrip.jsx itself is
// UNCHANGED and untouched — only this screen's render call was removed.
// No approved compact placement exists yet in canonical docs; a new
// placement is EXPLICITLY DEFERRED, not designed in this batch.

// Overview — approved closeout structure (restored from the approved-design
// migration, commit 9644759):
//   LEFT   — Production Facts (ProductionDetails: the Overview view of the
//            same Production Record the Workspace Inspector edits — POST
//            /people, role-level nationality; no duplicate input model)
//            + script-derived Production Requirements.
//   CENTER — Project Globe (the production Globe3D engine, unmodified,
//            graphite/obsidian direction) + Production Options: up to six
//            classified structure cards (Overview UI contract batch —
//            see IncentiveIntelligence.jsx), selecting one opens the
//            detailed scenario view.
//   RIGHT  — Budget Rail (BudgetRail: collapsed-by-default traceability
//            view over the canonical pkg.register; each line opens the
//            account Inspector, which carries the real qualified /
//            partially-qualified / excluded state from the QPE engine —
//            nothing recalculated here).

export default function Overview() {
  const { projectId } = useParams();
  const { data, error, loading, refetch } = useCineGlobe(projectId);
  const navigate = useNavigate();
  const {
    openInspector, leadingStructureId, setLeadingStructureId,
    selectedJurisdiction, setSelectedJurisdiction,
  } = useAppState();
  const [globeMode, setGlobeMode] = useState("jurisdictions");
  const [hover, setHover] = useState(null);
  // Overview Globe hover data parity: same GlobeHoverCard/hoverRect pattern
  // ProjectGlobe.jsx uses to anchor the card near the hovered marker rather
  // than a fixed corner — canvasRef is the card's nearest positioned
  // ancestor (the Globe panel below), not the Globe3D canvas element itself.
  const [hoverRect, setHoverRect] = useState(null);
  const canvasRef = useRef(null);

  const allocated = data?.structures?.allocated_structures;

  // Globe data — identical derivation to ProjectGlobe.jsx and Workspace's
  // Map/Split modes. One globe engine for the whole app, never forked.
  // Same shared leadingStructureId/selectedJurisdiction as the Workspace —
  // choosing a leading structure or jurisdiction on either screen updates
  // both without a refresh. grossBudgetUsd is passed through identically to
  // ProjectGlobe.jsx: buildGlobeView's buildCountryHoverData needs it for
  // the hover card's "Incentive / Gross Budget" figure — without it, that
  // one field would silently read "Not available" on Overview even where
  // the full Project Globe page shows a real percentage for the same
  // jurisdiction, which is exactly the parity gap this fix closes.
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode } = useMemo(
    () => buildGlobeView(allocated, rankById, {
      mode: globeMode, leadingStructureId, selectedJurisdiction,
      grossBudgetUsd: data?.production?.gross_budget_usd ?? null,
    }),
    [allocated, rankById, globeMode, leadingStructureId, selectedJurisdiction, data?.production?.gross_budget_usd],
  );
  // Bad Hombres Overview Truthfulness / generic ingestion propagation:
  // this is the SAME real defect the Workspace dynamic FX slot had (see
  // CAPABILITY_LEDGER.md, "Workspace Display Regression Closeout") —
  // activeStructure() correctly returns null whenever there is neither a
  // producer-selected Leading structure nor a canonical rank-1 (a real,
  // common state: comparable_count:0 when a production's own base
  // jurisdiction is unpriceable), but the Budget card then had no
  // fallback and silently showed Credit/NPC as "—" even while a real Top
  // Priced candidate (and the Hero's own real Modeled Net Cost) already
  // existed. Falls back to the SAME bestPricedCandidate(allocated) the
  // Hero already uses for its own "Top Priced Candidate" state — never a
  // second "best" computation — so the Budget card and Hero can never
  // silently disagree about which structure they describe.
  const structure = allocated ? (activeStructure(allocated, leadingStructureId) || bestPricedCandidate(allocated)) : null;
  const structureIsLeading = allocated ? !!activeStructure(allocated, leadingStructureId) : false;

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, people, economics, facts } = data;
  const contingencyPctRaw = facts?.answers?.contingency_expected_utilization_pct;
  const contingencyPct = contingencyPctRaw == null ? null : Number(contingencyPctRaw);

  // Production Options card click — same inspect pattern Scenarios.jsx
  // already uses (open the structure's first segment, or its
  // recommendation if it has no segments yet).
  function openIntelligenceCard(s) {
    setSelectedJurisdiction(s.primary_jurisdiction || s.participants?.[0] || null);
    const seg = s.segments?.[0];
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }

  function handleGlobeClick(pt) {
    const code = pt.jurisdictionCode || pt.id;
    setSelectedJurisdiction(code);
    const s = (structuresByCode.get(code) || [])[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }

  return (
    <div className="screen ovxg-screen">
      <div className="ovxg-grid">

        {/* ── LEFT — Production Facts + Production Requirements ─────────── */}
        <div className="ovxg-col">
          <ProductionDetails
            people={people}
            requirements={production.physical_requirements}
            refetch={refetch}
            projectId={projectId}
          />
        </div>

        {/* ── CENTER — Project Globe + jurisdiction snapshot strip ──────── */}
        <div className="ovxg-col">
          <section className="ovx-sec ovxg-globe-sec">
            <div className="oh">
              <b>Project Globe</b>
              <div className="wsx-viewtabs" style={{ marginLeft: 10 }}>
                <button className={globeMode === "jurisdictions" ? "active" : ""} onClick={() => setGlobeMode("jurisdictions")}>Jurisdictions</button>
                <button className={globeMode === "optimizer" ? "active" : ""} onClick={() => setGlobeMode("optimizer")}>Optimizer Overlay</button>
              </div>
              <button className="act" onClick={() => navigate(`/projects/${projectId}/globe`)}>Full screen →</button>
            </div>
            <div className="ovxg-globe-wrap dark-panel" style={{ position: "relative" }} ref={canvasRef}>
              <Globe3D
                points={points}
                arcs={arcs}
                height={420}
                pointRadius={0.2}
                polygonColors={polygonColors}
                selectedIso={selectedIso}
                hoveredIso={hover?.iso ?? null}
                selectedLat={selectedLat}
                selectedLng={selectedLng}
          focusLat={focusLat}
          focusLng={focusLng}
          focusDistance={focusDistance}
                // Overview Globe wrapper fix: the Inspector's 400px reframe
                // constant was copied from the full Project Globe page,
                // where the canvas spans nearly the full viewport width and
                // its right edge genuinely sits under the Inspector panel.
                // Here the Globe lives in the CENTER of a 3-column grid
                // (340px | 1fr | 340px) — the fixed-position Inspector
                // (right:0, width:400px) covers the RIGHT column (Budget
                // Rail, 340px) and the viewport margin beyond it, but never
                // reaches this narrower center-column canvas. Passing 400
                // anyway shrank the visible-width used for camera framing
                // (Globe3D's applySize: visibleW = canvasWidth -
                // obscuredRightPx) down to ~150px on a ~550px canvas,
                // producing a drastically zoomed-out, tiny sphere the
                // instant the Inspector opened. The Globe3D engine itself
                // is untouched — this column's canvas is simply never
                // obscured by the Inspector, at any grid breakpoint down to
                // the 1150px single-column collapse (a different layout
                // entirely, where the Inspector already sits over
                // everything as a full-width overlay and the Globe is not
                // usably interactive regardless of this value).
                obscuredRightPx={0}
                onPointClick={handleGlobeClick}
                // Overview Globe hover data parity: was `onPointHover={setHover}`,
                // which discarded Globe3D's second (rect) argument and fed a
                // local truncated tooltip (jurisdiction/statusLabel/role only —
                // no program, rate, modeled incentive, or NPC). Now the same
                // two-argument handler ProjectGlobe.jsx uses, feeding the same
                // canonical GlobeHoverCard below — one hover-data contract, two
                // Globe embeds, no duplicated economic presentation.
                onPointHover={(pt, rect) => { setHover(pt); setHoverRect(pt ? rect : null); }}
              />
              {hover && (
                <GlobeHoverCard hover={hover} hoverRect={hoverRect} canvasRef={canvasRef} />
              )}
            </div>
          </section>

          <IncentiveIntelligence
            allocated={allocated}
            onSelect={openIntelligenceCard}
          />
        </div>

        {/* ── RIGHT — Budget Rail (the ONE canonical budget surface: real
             imported department/account breakdown, drill-down, and the
             compact contingency control — traceability over the canonical
             register when a structure has priced, department-grouped
             pkg.budget line items otherwise) ── */}
        <div className="ovxg-col">
          <BudgetRail
            production={production}
            register={pkg.register}
            budget={pkg.budget}
            structure={structure}
            structureIsLeading={structureIsLeading}
            economics={economics}
            projectId={projectId}
            contingencyPct={contingencyPct}
            onContingencySaved={refetch}
            onSelectAccount={(line, alloc) => openInspector("account", {
              ...line,
              crossRef: alloc ? [{
                structureId: structure.structure_id,
                structureLabel: structure.label,
                jurisdictionCode: alloc.jurisdictionCode,
                claimsIncentive: alloc.claimsIncentive,
                qpeUsd: alloc.included ? line.amount : 0,
                incentiveFloorUsd: alloc.creditContributionUsd,
              }] : [],
            })}
          />
        </div>

      </div>
    </div>
  );
}
