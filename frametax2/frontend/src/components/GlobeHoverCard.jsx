import { formatFullUsd, incentivePctOfGross, presentExclusionReason, relatedJurisdictions } from "../lib/globeHoverFormat";
import { shortBlockerReason } from "../lib/blockerDisposition";
import { jurisdictionName } from "../lib/format";
import { FAMILY_META } from "../lib/globeStructure";
import { certaintyLabel, missingFactsSummary, missingFactsTitle, potentialRows } from "../lib/incentivePotential";

// Overview Globe hover data parity: extracted verbatim from
// ProjectGlobe.jsx (the sole prior home of this component) so BOTH the full
// Project Globe page and the Overview-embedded Globe render from ONE
// canonical hover-data/presentation contract — no duplicated economic
// derivation, no second implementation to drift out of sync. Every figure
// below is still read straight off the `hover` object that globeData.js's
// buildCountryHoverData already attaches to each point (via buildGlobeView,
// which both screens call identically) — this file only presents it.
//
// PHASE 3B GLOBE CLOSEOUT (unchanged from ProjectGlobe.jsx): field-by-field
// template per the standing hover contract — "Program Name / Maximum
// Incentive / Modeled Incentive / NPC / Incentive / Gross Budget", each its
// own line, full dollar amounts, no abbreviation. "Maximum Incentive" is a
// single number (rate_ceiling — see globeData.js's buildCountryHoverData /
// globeHoverFormat.js's modeledRateInfo for why that field, not rate_floor,
// is the one that actually funds the dollar figures below it), stated once,
// as "Up to X%".
function RecommendedOrAlternativeBody({ hover }) {
  const b = hover.baseIncentive;
  // SINGLE_JURISDICTION_GLOBE_WIRING (2026-09-23): "Modeled Incentive" now
  // reads hover.incentiveUsd (the whole structure's real total across every
  // segment — the same figure NPC below is already derived from) rather
  // than hover.segmentIncentiveUsd (only the FIRST segment's own
  // contribution, e.g. just OFTTC's share of a real OFTTC+OCASE stack) —
  // the prior figure silently understated a same-jurisdiction program
  // stack's real modeled incentive and disagreed with the NPC shown right
  // below it. "Program" now discloses every real stacked program
  // (programDisplayNames), never only the first.
  const pctOfGross = incentivePctOfGross(hover.incentiveUsd, hover.grossBudgetUsd);
  const programLine = hover.programDisplayNames?.length ? hover.programDisplayNames.join(" + ") : (b ? b.programLabel : null);
  return (
    <>
      <div className="hover-field">
        <div className="text-tertiary small">Program</div>
        <div className="small">{programLine || "Not available"}</div>
      </div>
      <div className="hover-field">
        <div className="text-tertiary small">{hover.incentivePotential ? "Maximum rate" : "Maximum Incentive"}</div>
        <div className="small">{b?.ratePct != null ? `Up to ${b.ratePct}%` : "Not available"}</div>
      </div>
      {hover.incentivePotential ? <PotentialFields pot={hover.incentivePotential} /> : (
        <>
          <div className="hover-field">
            <div className="text-tertiary small">Modeled Incentive</div>
            <div className="small">{hover.incentiveUsd != null ? formatFullUsd(hover.incentiveUsd) : "Not available"}</div>
          </div>
          <div className="hover-field">
            <div className="text-tertiary small">NPC</div>
            <div className="small">{hover.npcUsd != null ? formatFullUsd(hover.npcUsd) : "Not priced"}</div>
          </div>
        </>
      )}
      <div className="hover-field">
        <div className="text-tertiary small">Incentive / Gross Budget</div>
        <div className="small">{pctOfGross || "Not available"}</div>
      </div>
    </>
  );
}

// MAXIMUM-POTENTIAL INCENTIVE CONTRACT: the shared served floor/maximum and confirmed/potential NPC
// rows (identical to the Workspace card and Inspector), rendered verbatim -- never recomputed here.
function PotentialFields({ pot }) {
  return (
    <>
      {potentialRows(pot).map((r) => (
        <div className="hover-field" key={r.key} data-potential-field={r.key}>
          <div className="text-tertiary small">{r.label}</div>
          <div className="small">{r.value != null ? formatFullUsd(r.value) : "Not established"}</div>
        </div>
      ))}
      <div className="hover-field" data-potential-field="status" title={missingFactsTitle(pot)}>
        <div className="text-tertiary small">Economics</div>
        <div className="small">{certaintyLabel(pot)} · {missingFactsSummary(pot, 1)}</div>
      </div>
    </>
  );
}

// Co-Production Opportunity: program (if one resolved despite the block),
// the structure's own real related jurisdictions, and an explicit,
// undisguised "not available" for the two figures this data model does not
// yet support — never a fabricated uplift or NPC.
function CoProductionBody({ hover }) {
  const b = hover.baseIncentive;
  const related = relatedJurisdictions({ participants: [hover.jurisdictionCode, ...hover.relatedCodes] }, hover.jurisdictionCode, jurisdictionName);
  return (
    <>
      <div className="hover-field">
        <div className="text-tertiary small">Program</div>
        <div className="small">
          {b ? `${b.programLabel}${b.ratePct != null ? (b.isBandCeiling ? ` · Up to ${b.ratePct}%` : ` · ${b.ratePct}%`) : ""}` : "Not available"}
        </div>
      </div>
      {related.length > 0 && (
        <div className="hover-field">
          <div className="text-tertiary small">Co-Production With</div>
          <div className="small">{related.map((r) => r.name).join(", ")}</div>
        </div>
      )}
      <div className="hover-field">
        <div className="text-tertiary small">Co-Production Potential</div>
        <div className="small">Not modeled yet</div>
      </div>
      <div className="hover-field">
        <div className="text-tertiary small">Best Modeled NPC</div>
        <div className="small">Not priced — structure is blocked</div>
      </div>
    </>
  );
}

// OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): Optimizer-mode hover is
// STRUCTURE-level, not jurisdiction-level — every marker currently on
// screen belongs to the SAME ONE selected structure (buildOptimizerPathway
// renders exactly one at a time), so hovering ANY of its markers shows that
// whole structure's real summary: recommendation status, structural family,
// this marker's own role in the routing chain, every participant, the
// complete program stack (component -> jurisdiction -> program, QPE,
// incentive), total incentive, NPC, and the exact SAVES/NEUTRAL/COSTS MORE
// delta with its threshold reason. Every figure reads verbatim from
// `hover.structureDetail` — the SAME buildCandidateDetail() shape the
// Inspector already uses for this exact structure — never re-derived here.
function OptimizerStructureBody({ hover }) {
  const d = hover.structureDetail;
  if (!d) return <div className="hover-field"><div className="small">Not available from source data</div></div>;
  const deltaLabel = d.recommendation_status === "COSTS_MORE" ? "Costs more than Current Location"
    : d.recommendation_status === "NEUTRAL" ? "Same as Current Location"
    : d.recommendation_status === "BASELINE_UNRESOLVED" ? "Savings vs. Current Location"
    : "Saves vs. Current Location";
  return (
    <>
      {hover.role && (
        <div className="hover-field">
          <div className="text-tertiary small">Role</div>
          <div className="small">{hover.role}</div>
        </div>
      )}
      <div className="hover-field">
        <div className="text-tertiary small">Participants</div>
        <div className="small">{(d.participants || []).map(jurisdictionName).join(", ") || "Not available"}</div>
      </div>
      <div className="hover-field">
        <div className="text-tertiary small">Programs</div>
        <div className="small">
          {d.components?.length
            ? d.components.map((c) => `${jurisdictionName(c.code)}${c.program_slug ? ` · ${c.program_slug.replace(/_/g, " ")}` : ""}`).join("; ")
            : "Not available from source data"}
        </div>
      </div>
      {d.incentive_potential ? <PotentialFields pot={d.incentive_potential} /> : (
        <>
          <div className="hover-field">
            <div className="text-tertiary small">Total incentive</div>
            <div className="small">{d.incentive_usd != null ? formatFullUsd(d.incentive_usd) : "Not available"}</div>
          </div>
          <div className="hover-field">
            <div className="text-tertiary small">NPC</div>
            <div className="small">{d.npc_usd != null ? formatFullUsd(d.npc_usd) : "Not priced"}</div>
          </div>
        </>
      )}
      {d.recommendation_status && (
        <div className="hover-field">
          <div className="text-tertiary small">{deltaLabel}</div>
          <div className="small">
            {d.recommendation_status === "BASELINE_UNRESOLVED" || d.savings_vs_current_usd == null
              ? "Not available from source data"
              : formatFullUsd(Math.abs(d.savings_vs_current_usd))}
          </div>
        </div>
      )}
    </>
  );
}

// Excluded: one line answering "why isn't this an option" — the backend's
// own real discovery-examination reason, truncated to its first sentence
// and stripped of raw snake_case tokens (see globeHoverFormat.js's
// presentExclusionReason for exactly what transform is applied and why it
// is NOT a fabricated category enum).
function ExcludedBody({ hover }) {
  const reason = presentExclusionReason(hover.excludedReason) || "Current production constraints";
  return (
    <div className="hover-field">
      <div className="text-tertiary small">Reason</div>
      <div className="small">{reason}</div>
    </div>
  );
}

// GLOBE_WIRING_REMEDIATION (2026-10-01): the Optimizer-mode jurisdiction
// record. Every visible Optimizer marker (route or not) states ITS OWN
// jurisdiction's identity and strongest canonical category, the best
// associated structure with NPC/savings when priced, how many structures it
// represents per category, and -- when nothing priced exists -- the exact
// canonical blocker disposition and the engine's own reason. Never a generic
// "blocked", never blank when canonical data exists.
function CategoryCounts({ counts }) {
  if (!counts) return null;
  const parts = [
    counts.recommended ? `${counts.recommended} leading/strong` : null,
    counts.evaluated ? `${counts.evaluated} reference` : null,
    counts.needsFacts ? `${counts.needsFacts} needs facts` : null,
    counts.blocked ? `${counts.blocked} unavailable` : null,
  ].filter(Boolean);
  return (
    <div className="hover-field">
      <div className="text-tertiary small">Structures represented</div>
      <div className="small">{parts.length ? parts.join(" · ") : "None"}</div>
    </div>
  );
}

function JurisdictionRecordBody({ hover, hidePotential = false }) {
  const priced = hover.npcUsd != null;
  const reason = shortBlockerReason(hover.blockerReason || hover.excludedReason);
  return (
    <>
      <div className="hover-field">
        <div className="text-tertiary small">Best associated structure</div>
        <div className="small">{hover.structureLabel || "Not available"}</div>
      </div>
      {hover.structureStatusLabel && (
        <div className="hover-field">
          <div className="text-tertiary small">Structure status</div>
          <div className="small">{hover.structureStatusLabel}</div>
        </div>
      )}
      {priced ? (
        <>
          {hover.status === "amber" && hover.blockerReason && (
            <div className="hover-field" data-conditional-on>
              <div className="text-tertiary small">Conditional on</div>
              <div className="small">{String(hover.blockerReason).replace(/^MISSING_LOCATION_CAPABILITY_DATA:\s*/, "Missing location capability data: ").replace(/_NOT_ASSESSABLE/g, " (not assessable)").replace(/_/g, " ").toLowerCase()}</div>
            </div>
          )}
          {hidePotential ? null : hover.incentivePotential ? <PotentialFields pot={hover.incentivePotential} /> : (
            <div className="hover-field">
              <div className="text-tertiary small">NPC</div>
              <div className="small">{formatFullUsd(hover.npcUsd)}</div>
            </div>
          )}
          {hover.savingsUsd != null && (
            <div className="hover-field">
              <div className="text-tertiary small">{hover.savingsUsd >= 0 ? "Saves vs. Current Location" : "Costs more than Current Location"}</div>
              <div className="small">{formatFullUsd(Math.abs(hover.savingsUsd))}</div>
            </div>
          )}
        </>
      ) : (
        <>
          {hover.blockerLabel && (
            <div className="hover-field">
              <div className="text-tertiary small">Why not priced</div>
              <div className="small">{hover.blockerLabel}</div>
            </div>
          )}
          <div className="hover-field">
            <div className="text-tertiary small">{hover.status === "amber" ? "Facts needed" : "Canonical reason"}</div>
            <div className="small">{reason || "Not priced — see Inspector"}</div>
          </div>
          {hover.blockerDetail && (
            <div className="hover-field" data-blocker-detail>
              <div className="text-tertiary small">Guaranteed floor</div>
              <div className="small">{hover.blockerDetail.guaranteed_floor}{hover.blockerDetail.potential_ceiling_rate != null ? ` · ceiling up to ${Math.round(hover.blockerDetail.potential_ceiling_rate * 100)}%` : ""}</div>
              {hover.blockerPotential?.maximum_supported_incentive_usd != null && (
                <div className="small" data-blocker-potential>
                  Maximum potential {formatFullUsd(hover.blockerPotential.maximum_supported_incentive_usd)} (not guaranteed) · potential NPC {formatFullUsd(hover.blockerPotential.potential_npc_usd)}
                </div>
              )}
              {(hover.blockerContentGates || []).filter((g) => g.status === "NOT_ON_FILE").length > 0 && (
                <div className="small" data-blocker-content-gates>
                  Content / approvals not on file: {(hover.blockerContentGates || []).filter((g) => g.status === "NOT_ON_FILE").map((g) => g.kind.toLowerCase().replace(/_/g, " ")).slice(0, 3).join(", ")}
                </div>
              )}
              {(hover.blockerDetail.unresolved_propositions || []).filter((p) => !String(p.kind || "").startsWith("content_gate_")).slice(0, 3).map((p) => (
                <div className="small" key={p.condition_id} data-blocker-proposition>
                  {p.fact_key ? `${p.fact_key}: ${p.stored_value == null ? "not on file" : p.stored_value}` : p.description}
                </div>
              ))}
            </div>
          )}
        </>
      )}
      <CategoryCounts counts={hover.categoryCounts} />
    </>
  );
}

// Aggregated (non-route) marker: the jurisdiction record plus an explicit
// note that it is a status summary, not the selected route.
function AggregatedUniverseBody({ hover }) {
  return (
    <>
      <JurisdictionRecordBody hover={hover} />
      <div className="hover-field">
        <div className="text-tertiary small">Selected route</div>
        <div className="small">Does not use this jurisdiction</div>
      </div>
    </>
  );
}

// A jurisdiction on the selected route: its own record first (identity/
// category never overwritten by the route), then the route's own role and
// structure summary.
function RouteJurisdictionBody({ hover }) {
  return (
    <>
      {/* The selected route's own structure economics render once, below (OptimizerStructureBody). */}
      <JurisdictionRecordBody hover={hover} hidePotential={!!hover.structureDetail?.incentive_potential} />
      <div className="hover-field">
        <div className="text-tertiary small">Selected route</div>
        <div className="small">{hover.role || "Participating jurisdiction"}</div>
      </div>
      <OptimizerStructureBody hover={hover} />
    </>
  );
}

// Anchors the hover card near the hovered marker's own on-screen box
// (Globe3D passes it through unmodified from the CSS2D hit-target's
// getBoundingClientRect()) rather than a fixed panel corner. Clamped to stay
// inside the canvas panel on every edge — no floating-ui/popper dependency;
// a fixed approximate card width is enough for a compact, single-purpose
// card that never wraps to more than a few short lines.
const HOVER_CARD_W = 260;
const HOVER_CARD_MARGIN = 10;
function hoverCardStyle(hoverRect, canvasEl) {
  if (!hoverRect || !canvasEl) return { display: "none" };
  const box = canvasEl.getBoundingClientRect();
  let left = hoverRect.left - box.left + hoverRect.width / 2 + HOVER_CARD_MARGIN;
  let top = hoverRect.top - box.top - 8;
  left = Math.max(HOVER_CARD_MARGIN, Math.min(left, box.width - HOVER_CARD_W - HOVER_CARD_MARGIN));
  top = Math.max(HOVER_CARD_MARGIN, Math.min(top, box.height - 168));
  return { left, top, width: HOVER_CARD_W };
}

// STRUCTURE-AWARE GLOBE (2026-10-01): the previewed structure's story -- exact structural family (accent), anchor /
// principal, component destinations and routed spend, actionability + the specific blocker, and "1 of N structures"
// with family counts. Every value is a served canonical field read verbatim.
function StructureStory({ story, locked }) {
  const dot = (hex) => <span aria-hidden="true" style={{ display: "inline-block", width: 9, height: 9, borderRadius: 2, background: hex, marginRight: 5 }} />;
  const counts = story.familyCounts ? Object.entries(story.familyCounts) : [];
  return (
    <div className="hover-structure-story" data-structure-story data-structure-family={story.family} data-structure-identity={story.identity || ""}
      style={{ marginTop: 8, paddingTop: 6, borderTop: `2px solid ${story.accent}` }}>
      <div className="small" style={{ fontWeight: 600 }} data-story-field="family">
        {dot(story.accent)}{story.accentSecondary ? dot(story.accentSecondary) : null}{story.familyLabel}
      </div>
      <div className="text-tertiary small" data-story-field="position">
        Structure {story.position} of {story.total}{locked ? " · locked" : story.total > 1 ? " · click to lock, click again to cycle" : " · click to lock"}
      </div>
      {story.principal && (
        <div className="hover-field">
          <div className="text-tertiary small">{story.shape === "peer" || story.shape === "peer_plus_branches" ? "Principal" : "Anchor / principal"}</div>
          <div className="small" data-story-field="principal">{jurisdictionName(story.principal)}</div>
        </div>
      )}
      {story.routes.length > 0 && (
        <div className="hover-field">
          <div className="text-tertiary small">{story.shape === "hub_and_spoke" ? "Routes (hub and spoke)" : "Routes"}</div>
          {story.routes.map((r, i) => (
            <div className="small" key={`${r.from}-${r.to}-${i}`} data-story-field="route">
              {jurisdictionName(r.from)} {r.directed ? "→" : "↔"} {jurisdictionName(r.to)}{r.label ? ` · ${r.label}` : ""}
            </div>
          ))}
        </div>
      )}
      {story.layered && (
        <div className="small text-tertiary" data-story-field="layered">Layered programs in one jurisdiction (no geographic route)</div>
      )}
      <div className="hover-field">
        <div className="text-tertiary small">Status</div>
        <div className="small" data-story-field="status">{story.statusLabel}</div>
      </div>
      {story.blockerText && (
        <div className="hover-field">
          <div className="text-tertiary small">Blocker / facts needed</div>
          <div className="small" data-story-field="blocker">{story.blockerText}</div>
        </div>
      )}
      {counts.length > 1 && (
        <div className="text-tertiary small" data-story-field="family-counts">
          Here: {counts.map(([f, n]) => `${n} ${FAMILY_META[f]?.label?.toLowerCase() || f}`).join(" · ")}
        </div>
      )}
    </div>
  );
}

// The canonical Globe hover card — jurisdiction / category, then the
// Recommended-Alternative / Co-Production / Excluded body variant. `canvasRef`
// is the panel the card is positioned relative to (the full Project Globe's
// `.globe-screen-canvas` or Overview's `.ovxg-globe-wrap` — either works,
// both are just the nearest positioned ancestor).
export default function GlobeHoverCard({ hover, hoverRect, canvasRef }) {
  // OPTIMIZER_GLOBE_WORKSPACE_WIRING (2026-09-25): Optimizer-mode points
  // carry no `jurisdictionName`/`fullStatusLabel` (those are the Single
  // Jurisdiction per-country hover contract, built by buildCountryHoverData)
  // — the title is the structure's own real label, and the status line is
  // its real recommendation-status text (optimizerStatusLabel — "Best
  // Recommendation"/"Other Recommended"/"Evaluated Alternative" — the SAME
  // vocabulary the legend, side-list dot, and Inspector all agree with).
  const isOptimizer = hover.mode === "optimizer" || hover.isAggregatedUniverseMarker;
  const isAggregated = !!hover.isAggregatedUniverseMarker;
  const isRoute = isOptimizer && !isAggregated;
  return (
    <div className="globe-tooltip" role="status" data-hover-iso={hover.iso || hover.isoA2 || ""} style={{ ...hoverCardStyle(hoverRect, canvasRef.current), pointerEvents: "none" }}>
      <strong>{hover.jurisdictionName || hover.name}</strong>
      <div className="text-tertiary small" style={{ marginBottom: 6 }}>
        {hover.fullStatusLabel || hover.optimizerStatusLabel}
        {isRoute && hover.familyLabel ? ` · ${hover.familyLabel}` : ""}
      </div>
      {isAggregated ? (
        <AggregatedUniverseBody hover={hover} />
      ) : isRoute ? (
        <RouteJurisdictionBody hover={hover} />
      ) : hover.status === "silver" ? (
        <ExcludedBody hover={hover} />
      ) : hover.status === "amber" ? (
        <CoProductionBody hover={hover} />
      ) : (
        <RecommendedOrAlternativeBody hover={hover} />
      )}
      {hover.structureStory && <StructureStory story={hover.structureStory} locked={!!hover.structureLocked} />}
    </div>
  );
}
