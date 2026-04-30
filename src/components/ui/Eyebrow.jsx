export default function Eyebrow(props) {
  return (
    <div style={{
      fontFamily:"'DM Mono',monospace",
      fontSize:".7rem",
      letterSpacing:".25em",
      color:"#C9A84C",
      textTransform:"uppercase",
      marginBottom: props.mb || "1rem"
    }}>
      {props.children}
    </div>
  );
}
