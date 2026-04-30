import { useState } from "react";

export default function SavePrompt(props) {
  var [label, setLabel] = useState(props.defaultLabel || "");
  var [saved, setSaved] = useState(false);
  function doSave() {
    props.onSave(label);
    setSaved(true);
    setTimeout(function() { setSaved(false); }, 2500);
  }
  if (saved) {
    return <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".78rem", color:"#5A9A5A", textAlign:"center", padding:".75rem" }}>Saved to Library</div>;
  }
  return (
    <div>
      <div style={{ fontFamily:"'DM Mono',monospace", fontSize:".72rem", color:"#8A8070", marginBottom:".4rem" }}>Save this analysis</div>
      <input
        value={label}
        onChange={function(e) { setLabel(e.target.value); }}
        onKeyDown={function(e) { if (e.key === "Enter") doSave(); }}
        style={{ width:"100%", background:"#0A0A0A", border:"1px solid #2A2520", color:"#F0EAD6", fontFamily:"'Jost',sans-serif", fontSize:".85rem", padding:".6rem .85rem", outline:"none", marginBottom:".5rem" }}
      />
      <button onClick={doSave}
        style={{ background:"#C9A84C", color:"#080808", border:"none", fontFamily:"'Jost',sans-serif", fontSize:".8rem", fontWeight:700, letterSpacing:".08em", padding:".7rem 1.25rem", cursor:"pointer", width:"100%", textTransform:"uppercase" }}>
        Save to Library
      </button>
    </div>
  );
}
