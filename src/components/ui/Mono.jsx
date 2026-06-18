export default function Mono(props) {
  return (
    <span style={{
      fontFamily:"'DM Mono',monospace",
      color: props.color || "#8A8070",
      fontSize: props.size || ".75rem"
    }}>
      {props.children}
    </span>
  );
}
