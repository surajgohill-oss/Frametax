import { COUNTRIES } from "../constants.js";

export default function AnalyzingScreen(props) {
  var { cidx, lStep } = props;
  return (
    <div className="ld">
      <div className="ring" />
      <div>
        <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2rem", color:"#F0EAD6", textAlign:"center" }}>Researching global incentives</h2>
        <p style={{ fontFamily:"'DM Mono',monospace", color:"#C9A84C", fontSize:".8rem", textAlign:"center", marginTop:".5rem", letterSpacing:".15em" }}>{"Scanning " + COUNTRIES[cidx] + "..."}</p>
      </div>
      <div style={{ display:"flex", flexDirection:"column", gap:".6rem", width:340 }}>
        {["Scanning script for location requirements","Searching IMDb for cast & director","Reading budget origin & rate base","Scanning 100+ global incentive programs","Running treaty & stacking optimizer"].map(function(s, i) {
          return (
            <div key={i} style={{ display:"flex", alignItems:"center", gap:".75rem", fontFamily:"'DM Mono',monospace", fontSize:".8rem", color:i < lStep ? "#C9A84C" : i === lStep ? "#F0EAD6" : "#8A8070" }}>
              <div style={{ width:6, height:6, borderRadius:"50%", background:"currentColor", flexShrink:0 }} />
              {s}
            </div>
          );
        })}
      </div>
      <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070" }}>Takes 30-60 seconds. Researching live data.</p>
    </div>
  );
}
