export default function ErrBox(props) {
  if (!props.msg) return null;
  return (
    <div style={{
      background:"rgba(180,40,40,.1)",
      border:"1px solid rgba(180,40,40,.3)",
      padding:"1rem 1.25rem",
      color:"#E07070",
      fontSize:".82rem",
      marginBottom:"1.5rem",
      fontFamily:"'DM Mono',monospace",
      lineHeight:1.6
    }}>
      {props.msg}
    </div>
  );
}
