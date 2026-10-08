import { Money } from "../lib/format";
import { missingFactsSummary, missingFactsTitle } from "../lib/incentivePotential";

// ECONOMIC WELL (2026-10-08) -- the ONE presentation of the served maximum-potential / confirmed
// incentive contract, shared by Workspace's scenario cards and Overview's Featured Structures cards.
// MAXIMUM POTENTIAL NPC is the dominant figure (the optimization target) with the maximum potential
// incentive beneath it; CONFIRMED NPC / CONFIRMED INCENTIVE are the secondary comparison. The bar's
// denominator is the maximum potential incentive: green = confirmed share, amber = the rest of the
// maximum, all green only when confirmed equals the maximum. Every value is the served contract
// verbatim (readIncentivePotential); nothing here computes economics.

const pct = (part, whole) => (whole ? Math.max(0, Math.min(100, (part / whole) * 100)) : 0);

// Tag beside MAXIMUM POTENTIAL NPC: says plainly when the maximum is not yet confirmed.
export const potentialTag = (pot) =>
  pot.ceilingStatus === "NOT_ESTABLISHED" ? "Not established"
    : pot.ceilingStatus === "CONDITIONAL" || pot.certainty === "CONDITIONAL" ? "Conditional"
      : null;

// One concise line for NEEDED TO REACH MAXIMUM; authority citations and full detail stay in the Inspector.
export const neededToReachMaximum = (pot) => {
  if (pot.ceilingStatus === "CONFIRMED" && pot.certainty === "CONFIRMED") return "Nothing — maximum is confirmed";
  if (pot.ceilingStatus === "CONFIRMED") return "Award confirmation"; // max = confirmed; discretionary award risk open
  // first clause of the served fact only; the full text is the line's tooltip and the Inspector
  return missingFactsSummary(pot, 1).split(/ -- | — | \(/)[0];
};

export default function EconomicWell({ pot, className = "" }) {
  const confirmedShare = pct(pot.confirmedIncentive, pot.maxIncentive);
  const tag = potentialTag(pot);
  return (
    <div className={`wsx-econ${className ? ` ${className}` : ""}`} data-certainty={pot.certainty} data-ceiling-status={pot.ceilingStatus}>
      <div className="wsx-econ-max">
        <div className="wsx-econ-head">
          <span className="wsx-econ-label">Maximum potential NPC</span>
          {tag && <span className="wsx-econ-tag">{tag}</span>}
        </div>
        <div className="wsx-econ-figure"><Money value={pot.potentialNpc} bare /></div>
        <div className="wsx-econ-line"><span>Maximum potential incentive</span><span className="potential"><Money value={pot.maxIncentive} bare /></span></div>
      </div>
      <div className="wsx-econ-confirmed">
        <div className="wsx-econ-line npc"><span>Confirmed NPC</span><span><Money value={pot.confirmedNpc} bare /></span></div>
        <div className="wsx-econ-line"><span>Confirmed incentive</span><span className="incentive"><Money value={pot.confirmedIncentive} bare /></span></div>
      </div>
      {pot.maxIncentive != null && (
        <div className="wsx-range" role="img" aria-label={`Confirmed ${Math.round(confirmedShare)}% of maximum potential incentive`}>
          <u style={{ left: 0, width: `${confirmedShare}%` }} />
          <i style={{ left: `${confirmedShare}%`, right: 0 }} />
        </div>
      )}
      <div className="wsx-econ-needed" title={missingFactsTitle(pot)}>
        <span>Needed to reach maximum</span>
        <b>{neededToReachMaximum(pot)}</b>
      </div>
    </div>
  );
}
