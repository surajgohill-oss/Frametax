import { Money } from "../lib/format";
import { attainability, missingFactsTitle } from "../lib/incentivePotential";

// ECONOMIC WELL v2 (2026-10-08) -- the ONE interior presentation of the served maximum-potential / confirmed incentive
// contract, shared by Workspace's scenario cards and Overview's Featured Structures cards. Field order:
//   Maximum-potential NPC (dominant) -> Confirmed NPC -> confirmed + maximum-potential incentive ->
//   confirmed-versus-potential bar -> MFNI placeholder -> attainability (+ one requirement).
// Every figure is a served field verbatim (readIncentivePotential); nothing here computes economics. No rate, yield or
// percentage is shown on the card face (those stay in the Inspector), and the structure is never labelled "conditional":
// how reachable the maximum is is stated separately by attainability().

const fmt = (v) => `$${Math.round(v).toLocaleString("en-US")}`;
const pct = (part, whole) => (whole ? Math.max(0, Math.min(100, (part / whole) * 100)) : 0);

export default function EconomicWell({ pot, awardRisk = false, className = "", qualifiedSpend }) {
  const att = attainability(pot, awardRisk);
  const hasMax = pot.maxIncentive != null && pot.maxIncentive > 0;
  // jade = confirmed / maximum; amber = the unconfirmed delta / maximum (the remainder). All jade only when confirmed
  // equals the maximum; all amber when nothing is confirmed; an empty neutral track when no maximum exists.
  // The bar renders only from supported served values: a maximum AND a confirmed incentive. An unsupported side leaves an
  // empty neutral track (never an invented gap); a zero gap is valid (all jade).
  const supported = hasMax && pot.confirmedIncentive != null;
  const jade = supported ? pct(pot.confirmedIncentive, pot.maxIncentive) : 0;
  const amber = supported && jade < 100 ? 100 - jade : 0;
  return (
    <div className={`wsx-econ${className ? ` ${className}` : ""}`} data-ceiling-status={pot.ceilingStatus}>
      <div className="wsx-econ-max">
        <div className="wsx-econ-label">Maximum-potential NPC</div>
        <div className="wsx-econ-figure"><Money value={pot.potentialNpc} bare /></div>
      </div>
      <div className="wsx-econ-line npc"><span>NPC at confirmed incentive</span><span><Money value={pot.confirmedNpc} bare /></span></div>
      <div className="wsx-econ-incentives">
        <div className="wsx-econ-line"><span>Confirmed incentive</span><span className="incentive"><Money value={pot.confirmedIncentive} bare /></span></div>
        <div className="wsx-econ-line"><span>Maximum-potential incentive</span><span><Money value={pot.maxIncentive} bare /></span></div>
        {qualifiedSpend !== undefined && (
          <div className="wsx-econ-line"><span>Qualified spend</span><span><Money value={qualifiedSpend} bare /></span></div>
        )}
      </div>
      {/* MFNI: not wired. One honest row; no post-MFNI figure and no editor until a canonical adjustment owner is served. */}
      <div className="wsx-econ-mfni" data-mfni="not-modeled">
        <div className="wsx-econ-line"><span>MFNI</span><span>Not yet modeled</span></div>
      </div>
      <div className="wsx-bar-wrap">
        <div
          className="wsx-bar"
          role="img"
          aria-label={supported
            ? `Incentive composition: confirmed ${fmt(pot.confirmedIncentive)} of maximum-potential ${fmt(pot.maxIncentive)}${amber > 0 ? `, additional conditional ${fmt(pot.maxIncentive - pot.confirmedIncentive)}` : ""}`
            : "Incentive composition not established"}
        >
          {jade > 0 && <span className="jade" style={{ flexGrow: jade }} />}
          {amber > 0 && <span className="amber" style={{ flexGrow: amber }} />}
        </div>
        <div className="wsx-bar-labels">
          <span className="jade">{jade > 0 ? <Money value={pot.confirmedIncentive} /> : ""}</span>
          <span className="amber">{amber > 0 && pot.upside != null ? <>+<Money value={pot.upside} /></> : ""}</span>
        </div>
      </div>
      <div className="wsx-econ-need" data-attainability={att.headline} title={missingFactsTitle(pot)}>
        <div className="wsx-econ-need-head">{att.headline}</div>
        <div className="wsx-econ-need-req">{att.requirement || ""}</div>
        <div className="wsx-econ-need-more">{att.more > 0 ? `+${att.more} more in Inspector` : ""}</div>
      </div>
    </div>
  );
}
