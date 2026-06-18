import { QUESTIONS } from "../constants.js";
import { Eyebrow, ErrBox, Mono, SecBtn, PrimaryBtn, GhostBtn } from "../components/ui/index.js";

export default function QAScreen(props) {
  var { qi, setQi, answers, tIn, setTIn, err, answerQ } = props;
  return (
    <div className="sc680 fu">
      <Eyebrow>Step 3 of 4 - Production Details</Eyebrow>
      <div style={{ display:"flex", gap:4, marginBottom:"2.5rem" }}>
        {QUESTIONS.map(function(_, i) {
          return <div key={i} style={{ flex:1, height:3, background:i < qi ? "#C9A84C" : i === qi ? "#F0EAD6" : "#2A2520", transition:"background .3s" }} />;
        })}
      </div>
      <ErrBox msg={err} />
      <Mono color="#C9A84C" size=".7rem">{"Question " + (qi+1) + " of " + QUESTIONS.length}</Mono>
      <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:"2rem", fontWeight:300, lineHeight:1.3, color:"#F0EAD6", marginBottom:"2rem", marginTop:".5rem" }}>{QUESTIONS[qi].label}</h2>

      {QUESTIONS[qi].options ? (
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))", gap:".75rem", marginBottom:"2rem" }}>
          {QUESTIONS[qi].options.map(function(opt) {
            var sel = answers[QUESTIONS[qi].id] === opt;
            return (
              <button key={opt} onClick={function() { answerQ(opt); }}
                style={{ padding:".9rem 1.2rem", border:"1px solid " + (sel ? "#C9A84C" : "#2A2520"), background:sel ? "rgba(201,168,76,.12)" : "transparent", color:sel ? "#C9A84C" : "#F0EAD6", fontFamily:"'Jost',sans-serif", fontSize:".85rem", cursor:"pointer", textAlign:"left", lineHeight:1.4 }}>
                {opt}
              </button>
            );
          })}
        </div>
      ) : (
        <div>
          <input
            type="text" value={tIn}
            placeholder={QUESTIONS[qi].ph}
            onChange={function(e) { setTIn(e.target.value); }}
            onKeyDown={function(e) { if (e.key === "Enter" && tIn.trim()) answerQ(tIn.trim()); }}
            style={{ width:"100%", background:"#0E0E0E", border:"1px solid #2A2520", color:"#F0EAD6", fontFamily:"'Jost',sans-serif", fontSize:"1rem", padding:".9rem 1.2rem", outline:"none", marginBottom:"1.5rem" }}
          />
          <div style={{ display:"flex", gap:"1rem" }}>
            <SecBtn onClick={function() { answerQ("Not specified"); }}>Skip</SecBtn>
            <PrimaryBtn onClick={function() { answerQ(tIn.trim() || "Not specified"); }}>Next</PrimaryBtn>
          </div>
        </div>
      )}

      {qi > 0 && <GhostBtn onClick={function() { setQi(qi-1); setTIn(""); }}>Previous</GhostBtn>}
    </div>
  );
}
