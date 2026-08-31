import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { useAppState } from "../../state/AppState";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import { buildGlobeView, activeStructure, bestPricedCandidate } from "../../lib/globeData";
import ProductionDetails from "../../components/ProductionDetails";
import BudgetRail from "../../components/BudgetRail";
import BudgetComposition from "../../components/BudgetComposition";
import ContingencyControl from "../../components/ContingencyControl";
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
    inspector, openInspector, leadingStructureId, setLeadingStructureId,
    selectedJurisdiction, setSelectedJurisdiction,
  } = useAppState();
  const [globeMode, setGlobeMode] = useState("jurisdictions");
  const [hover, setHover] = useState(null);

  const allocated = data?.structures?.allocated_structures;

  // Globe data — identical derivation to ProjectGlobe.jsx and Workspace's
  // Map/Split modes. One globe engine for the whole app, never forked.
  // Same shared leadingStructureId/selectedJurisdiction as the Workspace —
  // choosing a leading structure or jurisdiction on either screen updates
  // both without a refresh.
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode } = useMemo(
    () => buildGlobeView(allocated, rankById, { mode: globeMode, leadingStructureId, selectedJurisdiction }),
    [allocated, rankById, globeMode, leadingStructureId, selectedJurisdiction],
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
            <div className="ovxg-globe-wrap dark-panel" style={{ position: "relative" }}>
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
                // The app-level floating Inspector (--inspector-width=400px)
                // can cover the right edge of the viewport, including part of
                // this panel on narrower layouts — same reframe as Project
                // Globe, so a selected country never disappears behind it.
                obscuredRightPx={inspector ? 400 : 0}
                onPointClick={handleGlobeClick}
                onPointHover={setHover}
              />
              {hover && (
                <div className="globe-tooltip">
                  <strong>{hover.jurisdictionName}</strong>
                  <div className="text-tertiary small">{hover.statusLabel}</div>
                  {hover.role && <div className="text-tertiary small">{hover.role}</div>}
                </div>
              )}
            </div>
          </section>

          <IncentiveIntelligence
            allocated={allocated}
            onSelect={openIntelligenceCard}
          />
        </div>

        {/* ── RIGHT — Budget composition (imported, generic) + Contingency
             control (producer assumption) + Budget Rail (Modeled Economics,
             traceability over the canonical register) ── */}
        <div className="ovxg-col">
          <BudgetComposition
            production={production}
            budget={pkg.budget}
            onSelectLine={(line) => openInspector("budget-line", line)}
          />
          <ContingencyControl
            projectId={projectId}
            budget={pkg.budget}
            currentPct={contingencyPct}
            onSaved={refetch}
          />
          <BudgetRail
            production={production}
            register={pkg.register}
            structure={structure}
            structureIsLeading={structureIsLeading}
            economics={economics}
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
