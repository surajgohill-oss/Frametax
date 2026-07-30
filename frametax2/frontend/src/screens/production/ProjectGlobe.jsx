import { useMemo, useState } from "react";
import { useCineGlobe } from "../../lib/useCineGlobe";
import { Loading, ErrorBox } from "../../components/Async";
import Globe3D from "../../components/Globe3D";
import { buildGlobeView, structureTier, STATUS_HEX } from "../../lib/globeData";
import GlobeFixtureBadge from "../../components/GlobeFixtureBadge";
import { useAppState } from "../../state/AppState";
import { Money, humanizeToken } from "../../lib/format";

// Project Globe — this production's structures and their routing on the
// canonical globe. Same live model as the Workspace Map mode, given its own
// full section per the approved artifact nav. Country click opens the
// jurisdiction segment / structure recommendation in the Inspector.
//
// DIVISION OF LABOUR (Phase 2 closeout): the Globe VISUALIZES, the Inspector
// EXPLAINS. This screen therefore carries no legend and no figures in its
// hover card — see the hover card below and globeData's buildCountryHoverData.
export default function ProjectGlobe() {
  const { data, error, loading } = useCineGlobe();
  const { inspector, openInspector, leadingStructureId, selectedJurisdiction, setSelectedJurisdiction } = useAppState();
  const [globeMode, setGlobeMode] = useState("jurisdictions");
  const [hover, setHover] = useState(null);

  const allocated = data?.structures?.allocated_structures;
  const rankById = useMemo(() => {
    if (!allocated) return new Map();
    return new Map(allocated.ranking.map((r) => [r.structure_id, r]));
  }, [allocated]);
  const { points, arcs, polygonColors, selectedIso, selectedLat, selectedLng, focusLat, focusLng, focusDistance, structuresByCode, stateCounts } = useMemo(
    () => buildGlobeView(allocated, rankById, { mode: globeMode, leadingStructureId, selectedJurisdiction }),
    [allocated, rankById, globeMode, leadingStructureId, selectedJurisdiction],
  );

  if (loading) return <div className="screen"><Loading /></div>;
  if (error) return <div className="screen"><ErrorBox message={error} /></div>;

  function selectJurisdiction(code) {
    setSelectedJurisdiction(code);
    const s = (structuresByCode.get(code) || [])[0];
    if (!s) return;
    const seg = s.segments.find((sg) => sg.jurisdiction_code === code);
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }

  // Candidate cards already have their own exact structure in hand —
  // routing the click through selectJurisdiction()'s structuresByCode
  // lookup was wrong whenever multiple structures share a participant
  // (every "Mauritius + X" component structure shares MU as a
  // participant): structuresByCode.get(code)[0] silently resolved to
  // WHICHEVER structure happens to be first for that code, not the one
  // whose card was actually clicked — clicking the "routed to SA" card
  // could open the baseline structure's Inspector instead. This opens
  // THIS structure's own segment directly, and frames the jurisdiction
  // that makes this specific card distinct: the routed destination for a
  // component/treaty structure, or the primary shoot for a single-country
  // baseline.
  function selectStructure(s) {
    const routedTo = (s.participants || []).find((c) => c !== s.primary_jurisdiction);
    const code = routedTo || s.primary_jurisdiction || s.participants?.[0];
    setSelectedJurisdiction(code);
    const seg = s.segments?.find((sg) => sg.jurisdiction_code === code) || s.segments?.[0];
    if (seg) openInspector("allocation-segment", { ...seg, structureLabel: s.label });
    else if (s.recommendation) openInspector("structure-recommendation", s.recommendation);
  }

  return (
    <div className="globe-screen">
      {/* Renders nothing unless the development-only visual fixture is
          explicitly enabled. Its counts panel is the permitted dev diagnostic
          that proves the four-state distribution during verification. */}
      <GlobeFixtureBadge counts={stateCounts} />
      <div className="globe-screen-context">
        <p className="screen-eyebrow">Project Globe</p>
        {/* "Candidate jurisdictions" was the previous engine's framing — a
            database of things examined. This production's real unit of
            decision is the production structure, which is also what the list
            below and the Inspector both open onto. */}
        <h1 className="serif" style={{ fontSize: 20 }}>Production structures</h1>
        <p className="text-tertiary small">
          The recommended structure for this production, its optimized alternatives,
          and the opportunities still to unlock.
        </p>
        <div className="wsx-viewtabs" style={{ marginBottom: 10 }}>
          <button className={globeMode === "jurisdictions" ? "active" : ""} onClick={() => setGlobeMode("jurisdictions")}>Jurisdictions</button>
          <button className={globeMode === "optimizer" ? "active" : ""} onClick={() => setGlobeMode("optimizer")}>Optimizer Overlay</button>
        </div>
        <div className="sc-jurlist">
          {/* Rank-first ordering — mirrors Workspace/Scenarios (visibleStructures),
              so a producer scanning this list sees the leading option first
              instead of raw generation order. Unranked candidates keep their
              original order after every ranked one. */}
          {[...allocated.structures]
            .sort((a, b) => (rankById.get(a.structure_id)?.rank ?? Infinity) - (rankById.get(b.structure_id)?.rank ?? Infinity))
            .map((s) => {
              // Card <-> Globe selection sync: a card is "active" when the
              // jurisdiction that makes IT distinct (its routed destination,
              // or its primary shoot for a single-country baseline — same
              // rule selectStructure() uses) is the currently selected
              // jurisdiction, so the mapping is symmetric in both directions.
              const routedTo = (s.participants || []).find((c) => c !== s.primary_jurisdiction);
              const code = routedTo || s.primary_jurisdiction || s.participants?.[0];
              const active = code && code === selectedJurisdiction;
              return (
                <div
                  className={`portfolio-chip${active ? " active" : ""}`}
                  key={s.structure_id}
                  onClick={() => selectStructure(s)}
                >
                  {/* Inline colour from the Globe's own STATUS_HEX, not the
                      ".dot" CSS class — that class pulls from unrelated
                      app-wide --gold/--jade/--silver/--amber tokens (a
                      different palette used by every other tier dot in the
                      app), which meant this card's dot and the Globe's own
                      fill for the same jurisdiction never actually matched
                      colours despite sharing a category name. */}
                  <span className="dot" style={{ background: STATUS_HEX[structureTier(s, rankById)] }} />
                  <div>
                    <div className="row-title small">{s.label}</div>
                    <div className="row-sub">
                      {humanizeToken(s.structure_type)} · {s.is_fully_priced ? <Money value={s.npc_with_adjustments_usd} /> : `${s.blockers.length} blocker${s.blockers.length === 1 ? "" : "s"}`}
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      <div className="globe-screen-canvas" style={{ position: "relative" }}>
        <Globe3D
          points={points}
          arcs={arcs}
          // The stage owns the height (see --globe-stage-* tokens); 560 is now
          // only the floor. Previously a hardcoded 560 regardless of how much
          // vertical space the page actually had.
          autoHeight
          height={560}
          pointRadius={0.22}
          polygonColors={polygonColors}
          selectedIso={selectedIso}
          hoveredIso={hover?.iso ?? null}
          selectedLat={selectedLat}
          selectedLng={selectedLng}
          focusLat={focusLat}
          focusLng={focusLng}
          focusDistance={focusDistance}
          // Inspector floats over this screen (not docked — see AppState),
          // covering the right var(--inspector-width)=400px of the canvas.
          // Bias camera framing left so a selected country stays clear of it.
          obscuredRightPx={inspector ? 400 : 0}
          onPointClick={(pt) => selectJurisdiction(pt.jurisdictionCode || pt.id)}
          onPointHover={setHover}
        />
        {/* Inspector preview, not a second Inspector. Jurisdiction, semantic
            state, production role — the MEANING of what's under the cursor.
            The incentive and NPC figures this used to print are the
            Inspector's to explain (with their qualification trace, caps and
            citations); duplicating them here gave a producer two places to
            read the same number and one of them with no provenance. */}
        {hover && (
          <div className="globe-tooltip">
            <strong>{hover.jurisdictionName}</strong>
            <div className="text-tertiary small">{hover.statusLabel}</div>
            {hover.role && <div className="text-tertiary small">{hover.role}</div>}
          </div>
        )}
        <p className="globe-caption small" style={{ borderRadius: "0 0 var(--radius-lg) var(--radius-lg)" }}>
          {/* The overlay caption must describe what is actually on screen. It
              previously always promised "production routing", but when the
              recommended structure is single-jurisdiction there is no routing
              to show — the overlay correctly lights one jurisdiction and draws
              no arc, and the caption then read as a rendering failure. */}
          {globeMode === "optimizer"
            ? arcs.length > 0
              ? "Showing the recommended structure's production routing only."
              : "The recommended structure is single-jurisdiction — no routing to show."
            : arcs.length > 0
              ? "Dashed routes mark this production's real multi-jurisdiction structures."
              : "No multi-jurisdiction structure is currently priced for this production."}
        </p>
      </div>
    </div>
  );
}
