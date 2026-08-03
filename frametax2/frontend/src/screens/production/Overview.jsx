import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { useAppState } from "../../state/AppState";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import { buildGlobeView, activeStructure, buildCountryStatuses, buildCountryHoverData } from "../../lib/globeData";
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
//            graphite/obsidian direction) + the compact jurisdiction
//            snapshot strip: exactly four cards, each only jurisdiction /
//            incentive / net production cost; selecting one opens the
//            detailed scenario view.
//   RIGHT  — Budget Rail (BudgetRail: collapsed-by-default traceability
//            view over the canonical pkg.register; each line opens the
//            account Inspector, which carries the real qualified /
//            partially-qualified / excluded state from the QPE engine —
//            nothing recalculated here).

export default function Overview() {
  const { data, error, loading, refetch } = useCineGlobe();
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
  const structure = allocated ? activeStructure(allocated, leadingStructureId) : null;

  // Incentive Intelligence — ONE representative jurisdiction per canonical
  // category (Recommended/Alternatives/Co-Production Opportunities/
  // Excluded), read from the SAME per-jurisdiction data the Globe itself
  // renders (buildCountryStatuses + buildCountryHoverData — no second
  // derivation). Selection is a pure display choice over real data:
  //   gold   — the single rank-1 jurisdiction (there is always exactly one).
  //   jade   — the Alternative with the highest own-segment incentive.
  //   amber  — the first Co-Production Opportunity, if this production's
  //            real optimizer output has one (currently it does not — see
  //            IncentiveIntelligence.jsx's own comment for why).
  //   silver — an Excluded jurisdiction that carries a REAL discovery
  //            examination reason, so the card never shows an empty one.
  // `amber`/`silver` may legitimately be null; IncentiveIntelligence.jsx
  // renders an honest empty state rather than fabricating a card.
  // Computed BEFORE the loading/error early-return below — every hook in
  // this component must run unconditionally on every render (Rules of
  // Hooks), so no useMemo can sit after a conditional return.
  const countryStatuses = useMemo(
    () => buildCountryStatuses(allocated, rankById),
    [allocated, rankById],
  );
  const hoverData = useMemo(
    () => buildCountryHoverData(countryStatuses, data?.production?.gross_budget_usd),
    [countryStatuses, data],
  );
  const representatives = useMemo(() => {
    const entries = [...hoverData.values()];
    const byStatus = (s) => entries.filter((e) => e.status === s);
    const gold = byStatus("gold")[0] || null;
    const jade = byStatus("jade").sort(
      (a, b) => (b.segmentIncentiveUsd || 0) - (a.segmentIncentiveUsd || 0),
    )[0] || null;
    const amberAll = byStatus("amber");
    const amber = amberAll.find((e) => e.excludedReason || e.relatedCodes?.length) || amberAll[0] || null;
    const silverAll = byStatus("silver");
    const silver = silverAll.find((e) => e.excludedReason) || silverAll[0] || null;
    return { gold, jade, amber, silver };
  }, [hoverData]);

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  const { production, pkg, people, economics } = data;

  const structById = new Map((allocated?.structures || []).map((s) => [s.structure_id, s]));

  function openIntelligenceCard(entry) {
    setSelectedJurisdiction(entry.jurisdictionCode);
    const s = structById.get(entry.structureId);
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === entry.jurisdictionCode);
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
              <button className="act" onClick={() => navigate("/production/globe")}>Full screen →</button>
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
            representatives={representatives}
            onSelect={openIntelligenceCard}
          />
        </div>

        {/* ── RIGHT — Budget Rail (traceability over the canonical register) ── */}
        <div className="ovxg-col">
          <BudgetRail
            production={production}
            register={pkg.register}
            structure={structure}
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
