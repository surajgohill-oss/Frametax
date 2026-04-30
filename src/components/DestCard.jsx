import { fmt } from "../utils.js";
import Label from "./ui/Label.jsx";
import OverridePanel from "./OverridePanel.jsx";

export default function DestCard(props) {
  var dest = props.dest;
  var isTop = props.isTop;
  var budget = props.budget;
  var savings = (budget && dest.trueNetCost) ? fmt(budget - dest.trueNetCost) : null;
  var open = props.open;
  var setOpen = props.setOpen;
  var overrideData = props.overrideData;
  var overridePending = props.overridePending;
  var onRunOverride = props.onRunOverride;

  var hasFailedQuals = (dest.qualifications || []).some(function(q) {
    return q.status === "fail" || q.status === "partial";
  });

  function qColor(s) {
    if (s === "pass" || s === "likely_pass") return "#5A9A5A";
    if (s === "partial") return "#C97A1C";
    return "#E07070";
  }
  function qIcon(s) {
    if (s === "pass" || s === "likely_pass") return "OK";
    if (s === "partial") return "~";
    return "X";
  }

  var locFit = dest.locationFit || "";
  var locColor = "#C9A84C";
  if (locFit.toLowerCase().match(/excell|perfect|ideal/)) locColor = "#5A9A5A";
  if (locFit.toLowerCase().match(/poor|cannot|not suit/)) locColor = "#E07070";

  return (
    <div style={{ border:"1px solid " + (isTop ? "#C9A84C" : "#2A2520"), marginBottom:"1rem", overflow:"hidden" }}>
      <div
        onClick={function() { setOpen(!open); }}
        style={{ display:"flex", alignItems:"center", gap:"1.25rem", padding:"1.25rem 1.5rem", background:"#0C0C0C", cursor:"pointer" }}>
        <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.8rem", fontWeight:600, color:"#C9A84C", minWidth:"2.2rem", textAlign:"center" }}>{"#" + dest.rank}</div>
        <div style={{ flex:1 }}>
          <div style={{ display:"flex", alignItems:"center", gap:".5rem", flexWrap:"wrap" }}>
            <span style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.5rem", fontWeight:300, color:"#F0EAD6" }}>{dest.flag + " " + dest.country}</span>
            {dest.isPreferred && <span style={{ fontFamily:"'DM Mono',monospace", fontSize:".6rem", background:"rgba(201,168,76,.15)", color:"#C9A84C", border:"1px solid rgba(201,168,76,.3)", padding:".15rem .5rem" }}>REQUESTED</span>}
          </div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#8A8070", marginTop:".2rem" }}>{dest.incentiveProgram}</div>
          {locFit && <div style={{ display:"inline-block", fontFamily:"'DM Mono',monospace", fontSize:".7rem", padding:".2rem .55rem", marginTop:".3rem", background:locColor+"18", border:"1px solid "+locColor+"40", color:locColor }}>{"Location: " + locFit}</div>}
        </div>
        <div style={{ textAlign:"right", flexShrink:0 }}>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:"1.1rem", color:"#C9A84C" }}>{dest.creditRate}</div>
          {savings && <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#5A9A5A" }}>{"Save ~" + savings}</div>}
        </div>
        <div style={{ color:"#8A8070", marginLeft:".5rem" }}>{open ? "^" : "v"}</div>
      </div>

      {open && (
        <div style={{ padding:"1.25rem 1.5rem", borderTop:"1px solid #2A2520" }}>
          {dest.rateAdjustmentNote && (
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".75rem", color:"#C9A84C", background:"rgba(201,168,76,.05)", border:"1px solid rgba(201,168,76,.15)", padding:".6rem 1rem", marginBottom:"1rem" }}>
              {"Rate: " + dest.rateAdjustmentNote}
            </div>
          )}

          <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:".75rem", marginBottom:"1rem" }}>
            {[
              ["Local Cost", fmt(dest.localCostUSD), "#F0EAD6"],
              ["Tax Credit", "-" + fmt(dest.estimatedCredit), "#C9A84C"],
              ["Travel", "+" + fmt(dest.travelCost), "#F0EAD6"],
              ["True Net", fmt(dest.trueNetCost), "#5A9A5A"]
            ].map(function(row) {
              return (
                <div key={row[0]} style={{ background:"#0A0A0A", padding:".75rem", border:"1px solid #2A2520" }}>
                  <Label>{row[0]}</Label>
                  <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".9rem", color:row[2] }}>{row[1]}</div>
                </div>
              );
            })}
          </div>

          {dest.vsSavings && (
            <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".75rem", color:"#5A9A5A", background:"rgba(90,154,90,.08)", border:"1px solid rgba(90,154,90,.2)", padding:".4rem .85rem", display:"inline-block", marginBottom:"1rem" }}>
              {"Save " + dest.vsSavings + " (" + dest.vsPercent + ") vs home budget"}
            </div>
          )}

          {dest.exchangeRate && (
            <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#8A8070", marginBottom:".75rem" }}>
              {dest.exchangeRate + " - Currency risk: " + dest.currencyRisk}
            </p>
          )}

          {dest.qualifications && dest.qualifications.length > 0 && (
            <div>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", margin:"1rem 0 .5rem" }}>Qualification Analysis</div>
              {dest.qualifications.map(function(q, i) {
                return (
                  <div key={i} style={{ display:"flex", gap:".75rem", fontSize:".82rem", color:"#8A8070", padding:".35rem 0", borderBottom:"1px solid #141414", lineHeight:1.5 }}>
                    <span style={{ color:qColor(q.status), flexShrink:0, fontFamily:"'DM Mono',monospace", fontSize:".7rem" }}>{qIcon(q.status)}</span>
                    <span><strong style={{ color:"#F0EAD6" }}>{q.test}</strong>{" - " + q.detail}</span>
                  </div>
                );
              })}
            </div>
          )}

          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", margin:"1rem 0 .5rem" }}>Cost Eligibility</div>
          {[
            ["Above-the-Line", dest.atLStatus],
            ["Insurance & Bond", dest.insuranceStatus],
            ["Finance Costs", dest.financeStatus]
          ].map(function(row) {
            return (
              <div key={row[0]} style={{ display:"flex", gap:".75rem", fontSize:".82rem", color:"#8A8070", padding:".35rem 0", borderBottom:"1px solid #141414" }}>
                <span style={{ color:"#C9A84C", flexShrink:0, fontFamily:"'DM Mono',monospace", fontSize:".7rem" }}>*</span>
                <span><strong style={{ color:"#F0EAD6" }}>{row[0]}</strong>{" - " + (row[1] || "Check with local film commission")}</span>
              </div>
            );
          })}

          {dest.coproOpportunity && (
            <div style={{ marginTop:".75rem", fontSize:".82rem", color:"#8A8070" }}>{"Co-pro: " + dest.coproOpportunity}</div>
          )}

          {dest.qualGap && (
            <div style={{ background:"rgba(201,168,76,.06)", border:"1px solid rgba(201,168,76,.2)", padding:"1rem", marginTop:"1rem" }}>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", textTransform:"uppercase", letterSpacing:".1em", marginBottom:".4rem" }}>Optimization Opportunity</div>
              <div style={{ fontSize:".83rem", color:"#F0EAD6", lineHeight:1.6 }}>{dest.qualGap}</div>
            </div>
          )}

          {dest.structuringTip && (
            <div style={{ background:"rgba(90,154,90,.05)", border:"1px solid rgba(90,154,90,.2)", padding:"1rem", marginTop:".75rem" }}>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#5A9A5A", textTransform:"uppercase", letterSpacing:".1em", marginBottom:".4rem" }}>Structuring Recommendation</div>
              <div style={{ fontSize:".83rem", color:"#F0EAD6", lineHeight:1.6 }}>{dest.structuringTip}</div>
            </div>
          )}

          {dest.highlights && dest.highlights.length > 0 && (
            <div>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#C9A84C", letterSpacing:".15em", textTransform:"uppercase", margin:"1rem 0 .5rem" }}>Highlights</div>
              {dest.highlights.map(function(h, i) {
                return (
                  <div key={i} style={{ display:"flex", gap:".75rem", fontSize:".82rem", color:"#8A8070", padding:".35rem 0", borderBottom:"1px solid #141414" }}>
                    <span style={{ color:"#5A9A5A" }}>+</span>
                    <span>{h}</span>
                  </div>
                );
              })}
            </div>
          )}

          {hasFailedQuals && (
            <div style={{ marginTop:"1.25rem", borderTop:"1px solid #2A2520", paddingTop:"1.25rem" }}>
              {!overrideData && (
                <div style={{ display:"flex", gap:"1rem", alignItems:"center", flexWrap:"wrap" }}>
                  <div style={{ flex:1 }}>
                    <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#E07070", marginBottom:".25rem" }}>One or more qualifications flagged as fail or partial</div>
                    <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".68rem", color:"#8A8070" }}>Run a hypothetical override analysis assuming full qualification - see the full incentive, calculation methodology, and what steps are needed to actually qualify.</div>
                  </div>
                  <button
                    onClick={onRunOverride}
                    disabled={overridePending}
                    style={{ background: overridePending ? "#1A1A0A" : "rgba(201,168,76,.1)", border:"1px solid " + (overridePending ? "#3A3010" : "rgba(201,168,76,.4)"), color: overridePending ? "#5A5040" : "#C9A84C", fontFamily:"'DM Mono',monospace", fontSize:".75rem", padding:".65rem 1.25rem", cursor: overridePending ? "not-allowed" : "pointer", whiteSpace:"nowrap", letterSpacing:".06em" }}>
                    {overridePending ? "Analyzing..." : "Assume Qualification + Re-run"}
                  </button>
                </div>
              )}
              {overridePending && (
                <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#C9A84C", textAlign:"center", padding:"1rem", display:"flex", alignItems:"center", justifyContent:"center", gap:".75rem" }}>
                  <div style={{ width:14, height:14, borderRadius:"50%", border:"2px solid #2A2520", borderTopColor:"#C9A84C", animation:"spin 1s linear infinite" }} />
                  Running override analysis with full web research...
                </div>
              )}
              {overrideData && (
                <div>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:".5rem" }}>
                    <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#C9A84C", letterSpacing:".1em" }}>Override analysis complete</div>
                    <button onClick={onRunOverride} style={{ background:"transparent", border:"none", color:"#8A8070", fontFamily:"'DM Mono',monospace", fontSize:".68rem", cursor:"pointer" }}>Re-run override</button>
                  </div>
                  <OverridePanel data={overrideData} orig={dest} />
                </div>
              )}
            </div>
          )}

        </div>
      )}
    </div>
  );
}
