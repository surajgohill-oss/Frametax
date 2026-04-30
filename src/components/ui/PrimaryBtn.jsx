export default function PrimaryBtn(props) {
  return (
    <button
      onClick={props.onClick}
      disabled={props.disabled}
      style={{
        background: props.disabled ? "#3A3010" : "#C9A84C",
        color: props.disabled ? "#5A5040" : "#080808",
        fontFamily:"'Jost',sans-serif",
        fontSize:".85rem",fontWeight:700,
        letterSpacing:".1em",textTransform:"uppercase",
        padding:".9rem 2.5rem",border:"none",cursor:props.disabled?"not-allowed":"pointer"
      }}>
      {props.children}
    </button>
  );
}
