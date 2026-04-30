export default function GhostBtn(props) {
  return (
    <button onClick={props.onClick} style={{
      background:"transparent",color:"#8A8070",fontFamily:"'DM Mono',monospace",
      fontSize:".75rem",padding:".5rem 1rem",border:"none",cursor:"pointer"
    }}>
      {props.children}
    </button>
  );
}
