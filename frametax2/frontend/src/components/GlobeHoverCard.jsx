import { formatFullUsd, incentivePctOfGross, presentExclusionReason, relatedJurisdictions } from "../lib/globeHoverFormat";
import { jurisdictionName } from "../lib/format";

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
        <div className="text-tertiary small">Maximum Incentive</div>
        <div className="small">{b?.ratePct != null ? `Up to ${b.ratePct}%` : "Not available"}</div>
      </div>
      <div className="hover-field">
        <div className="text-tertiary small">Modeled Incentive</div>
        <div className="small">{hover.incentiveUsd != null ? formatFullUsd(hover.incentiveUsd) : "Not available"}</div>
      </div>
      <div className="hover-field">
        <div className="text-tertiary small">NPC</div>
        <div className="small">{hover.npcUsd != null ? formatFullUsd(hover.npcUsd) : "Not priced"}</div>
      </div>
      <div className="hover-field">
        <div className="text-tertiary small">Incentive / Gross Budget</div>
        <div className="small">{pctOfGross || "Not available"}</div>
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
      <div className="hover-field">
        <div className="text-tertiary small">Total incentive</div>
        <div className="small">{d.incentive_usd != null ? formatFullUsd(d.incentive_usd) : "Not available"}</div>
      </div>
      <div className="hover-field">
        <div className="text-tertiary small">NPC</div>
        <div className="small">{d.npc_usd != null ? formatFullUsd(d.npc_usd) : "Not priced"}</div>
      </div>
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
  const isOptimizer = hover.mode === "optimizer";
  return (
    <div className="globe-tooltip" style={hoverCardStyle(hoverRect, canvasRef.current)}>
      <strong>{isOptimizer ? (hover.structureDetail?.label || hover.name) : hover.jurisdictionName}</strong>
      <div className="text-tertiary small" style={{ marginBottom: 6 }}>
        {isOptimizer ? hover.optimizerStatusLabel : hover.fullStatusLabel}
        {isOptimizer && hover.familyLabel ? ` · ${hover.familyLabel}` : ""}
      </div>
      {isOptimizer ? (
        <OptimizerStructureBody hover={hover} />
      ) : hover.status === "silver" ? (
        <ExcludedBody hover={hover} />
      ) : hover.status === "amber" ? (
        <CoProductionBody hover={hover} />
      ) : (
        <RecommendedOrAlternativeBody hover={hover} />
      )}
    </div>
  );
}
