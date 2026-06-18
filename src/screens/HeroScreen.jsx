import { fmt } from "../utils.js";
import { Eyebrow, PrimaryBtn } from "../components/ui/index.js";

export default function HeroScreen(props) {
  var { library, setPage, setShowLib } = props;
  return (
    <div style={{ minHeight:"100vh", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", padding:"3rem 2rem", textAlign:"center" }}>
      <Eyebrow mb="2rem">Film Production Finance Intelligence</Eyebrow>
      <h1 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"clamp(2.8rem,7vw,5.5rem)", fontWeight:300, lineHeight:1.05, color:"#F0EAD6", marginBottom:"1.5rem" }}>
        Where in the world<br/>should you{" "}
        <em style={{ color:"#C9A84C", fontStyle:"italic" }}>film</em>?
      </h1>
      <p style={{ maxWidth:520, fontSize:"1rem", fontWeight:300, color:"#8A8070", lineHeight:1.7, marginBottom:"3rem" }}>
        Upload your budget. Our AI scans 100+ global tax incentive programs, rebases BTL costs to local rates, checks IMDb for attachments, and applies live FX to find exactly where your money goes furthest.
      </p>
      <div style={{ display:"flex", gap:"2.5rem", borderTop:"1px solid #2A2520", borderBottom:"1px solid #2A2520", padding:"1.5rem 2.5rem", marginBottom:"3rem", flexWrap:"wrap", justifyContent:"center" }}>
        {[["100+","Jurisdictions"],["Live","FX Rates"],["IMDb","Attachments"],["Full","Cost Rebase"]].map(function(pair) {
          return (
            <div key={pair[1]} style={{ textAlign:"center" }}>
              <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2rem", fontWeight:600, color:"#C9A84C" }}>{pair[0]}</div>
              <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".7rem", color:"#8A8070", letterSpacing:".12em", textTransform:"uppercase", marginTop:".2rem" }}>{pair[1]}</div>
            </div>
          );
        })}
      </div>
      <PrimaryBtn onClick={function() { setPage("upload"); }}>Upload Your Budget</PrimaryBtn>
      <p style={{ fontFamily:"'DM Mono',monospace", fontSize:".75rem", color:"#8A8070", marginTop:"1.5rem" }}>PDF  Movie Magic  CSV  Paste text</p>
      {library.length > 0 && (
        <button onClick={function() { setPage("upload"); setShowLib(true); }}
          style={{ marginTop:"1.5rem", background:"transparent", border:"1px solid #2A2520", color:"#8A8070", fontFamily:"'DM Mono',monospace", fontSize:".75rem", padding:".5rem 1.25rem", cursor:"pointer" }}>
          {"Open Library (" + library.length + " saved project" + (library.length !== 1 ? "s" : "") + ")"}
        </button>
      )}
    </div>
  );
}
