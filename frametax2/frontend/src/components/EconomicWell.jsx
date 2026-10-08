import { Money } from "../lib/format";
import { attainability, missingFactsTitle } from "../lib/incentivePotential";

// ECONOMIC WELL v2 (2026-10-08) -- the ONE interior presentation of the served maximum-potential / confirmed incentive
// contract, shared by Workspace's scenario cards and Overview's Featured Structures cards. Field order:
//   Maximum-potential NPC (dominant) -> Confirmed NPC -> confirmed + maximum-potential incentive ->
//   confirmed-versus-potential bar -> MFNI placeholder -> attainability (+ one requirement).
// Every figure is a served field verbatim (readIncentivePotential); nothing here computes economics. No rate, yield or
// percentage is shown on the card face (those stay in the Inspector), and the structure is never labelled "conditional":
// how reachable the maximum is is stated separately by attainability().

const pct = (part, whole) => (whole ? Math.max(0, Math.min(100, (part / whole) * 100)) : 0);

export default function EconomicWell({ pot, awardRisk = false, className = "" }) {
  const att = attainability(pot, awardRisk);
  const hasMax = pot.maxIncentive != null && pot.maxIncentive > 0;
  // jade = confirmed / maximum; amber = the unconfirmed delta / maximum (the remainder). All jade only when confirmed
  // equals the maximum; all amber when nothing is confirmed; an empty neutral track when no maximum exists.
  const jade = hasMax ? pct(pot.confirmedIncentive ?? 0, pot.maxIncentive) : 0;
  const amber = hasMax && jade < 100 ? 100 - jade : 0;
  return (
    <div className={`wsx-econ${className ? ` ${className}` : ""}`} data-ceiling-status={pot.ceilingStatus}>
      <div className="wsx-econ-max">
        <div className="wsx-econ-label">Maximum-potential NPC</div>
        <div className="wsx-econ-figure"><Money value={pot.potentialNpc} bare /></div>
      </div>
      <div className="wsx-econ-line npc"><span>Confirmed NPC</span><span><Money value={pot.confirmedNpc} bare /></span></div>
      <div className="wsx-econ-incentives">
        <div className="wsx-econ-line"><span>Confirmed incentive</span><span className="incentive"><Money value={pot.confirmedIncentive} bare /></span></div>
        <div className="wsx-econ-line"><span>Maximum-potential incentive</span><span><Money value={pot.maxIncentive} bare /></span></div>
      </div>
      <div className="wsx-bar-wrap">
        <div
          className="wsx-bar"
          role="img"
          aria-label={hasMax ? `Confirmed incentive of the maximum-potential incentive` : "No maximum-potential incentive established"}
        >
          {jade > 0 && <span className="jade" style={{ flexGrow: jade }} />}
          {amber > 0 && <span className="amber" style={{ flexGrow: amber }} />}
        </div>
        <div className="wsx-bar-labels">
          <span className="jade">{jade > 0 ? <Money value={pot.confirmedIncentive} /> : ""}</span>
          <span className="amber">{amber > 0 && pot.upside != null ? <>+<Money value={pot.upside} /></> : ""}</span>
        </div>
      </div>
      {/* MFNI placeholder: a stable reserved row. Not calculated and not modelled in this pass; when served data exists it
          becomes "MFNI ADJUSTMENT −$X" / "NPC AFTER MFNI $Y". Assumptions editing is not wired yet (next MFNI task). */}
      <div className="wsx-econ-mfni" data-mfni="not-modeled">
        <div className="wsx-econ-line"><span>MFNI ADJUSTMENT NOT YET MODELED</span><span /></div>
        <div className="wsx-econ-line"><span>NPC AFTER MFNI</span><span>—</span></div>
        <div className="wsx-econ-note">Assumptions editing not yet available</div>
      </div>
      <div className="wsx-econ-need" data-attainability={att.headline} title={missingFactsTitle(pot)}>
        <div className="wsx-econ-need-head">{att.headline}</div>
        <div className="wsx-econ-need-req">{att.requirement || ""}</div>
        <div className="wsx-econ-need-more">{att.more > 0 ? `+${att.more} more in Inspector` : ""}</div>
      </div>
    </div>
  );
}
