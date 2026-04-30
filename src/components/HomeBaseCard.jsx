import { useState } from "react";
import { fmt } from "../utils.js";
import Label from "./ui/Label.jsx";

export default function HomeBaseCard(props) {
  var hb = props.homeBase;
  var budget = props.budget;
  var [open, setOpen] = useState(false);
  if (!hb) return null;
  var hasIncentive = hb.estimatedCredit && hb.estimatedCredit > 0;
  return (
    <div style={{ border:"1px solid #3A3020", marginBottom:"1rem", background:"rgba(201,168,76,.02)" }}>
      <div onClick={function() { setOpen(!open); }}
        style={{ display:"flex", alignItems:"center", gap:"1.25rem", padding:"1.25rem 1.5rem", cursor:"pointer" }}>
        <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.4rem", fontWeight:300, color:"#8A8070", minWidth:"2.2rem", textAlign:"center" }}>HOME</div>
        <div style={{ flex:1 }}>
          <div style={{ display:"flex", alignItems:"center", gap:".5rem" }}>
            <span style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"1.5rem", fontWeight:300, color:"#8A8070" }}>{(hb.flag || "") + " " + hb.country}</span>
            <span style={{ fontFamily:"'DM Mono',monospace", fontSize:".6rem", background:"rgba(138,128,112,.1)", color:"#8A8070", border:"1px solid #2A2520", padding:".15rem .5rem" }}>BASELINE</span>
          </div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#8A8070", marginTop:".2rem" }}>{hb.incentiveProgram || (hasIncentive ? "Local incentive program" : "No applicable incentive program")}</div>
        </div>
        <div style={{ textAlign:"right", flexShrink:0 }}>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:"1.1rem", color: hasIncentive ? "#C9A84C" : "#8A8070" }}>{hb.creditRate || (hasIncentive ? "-" : "No credit")}</div>
          <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".74rem", color:"#F0EAD6" }}>{hb.trueNetCost ? "Net: " + fmt(hb.trueNetCost) : (budget ? "Net: " + fmt(budget) : "")}</div>
        </div>
        <div style={{ color:"#8A8070", marginLeft:".5rem" }}>{open ? "^" : "v"}</div>
      </div>
      {open && (
        <div style={{ padding:"1.25rem 1.5rem", borderTop:"1px solid #2A2520" }}>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:".75rem", marginBottom:"1rem" }}>
            {[
              ["Home Budget", fmt(budget), "#F0EAD6"],
              ["Home Credit", hasIncentive ? fmt(hb.estimatedCredit) : "None", hasIncentive ? "#C9A84C" : "#8A8070"],
              ["True Net at Home", fmt(hb.trueNetCost || budget), "#F0EAD6"]
            ].map(function(row) {
              return (
                <div key={row[0]} style={{ background:"#0A0A0A", padding:".75rem", border:"1px solid #2A2520" }}>
                  <Label>{row[0]}</Label>
                  <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".9rem", color:row[2] }}>{row[1]}</div>
                </div>
              );
            })}
          </div>
          {hb.notes && <p style={{ fontSize:".82rem", color:"#8A8070", lineHeight:1.6, marginBottom:".5rem" }}>{hb.notes}</p>}
          {hb.noIncentiveReason && !hasIncentive && (
            <div style={{ background:"rgba(224,112,112,.06)", border:"1px solid rgba(224,112,112,.2)", padding:".75rem 1rem", fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#E07070" }}>
              {hb.noIncentiveReason}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
