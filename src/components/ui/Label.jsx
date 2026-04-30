export default function Label(props) {
  return (
    <div style={{
      fontFamily:"'DM Mono',monospace",
      fontSize:".68rem",
      letterSpacing:".12em",
      textTransform:"uppercase",
      color:"#8A8070",
      marginBottom:".3rem"
    }}>
      {props.children}
    </div>
  );
}
