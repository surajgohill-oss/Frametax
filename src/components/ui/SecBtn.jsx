export default function SecBtn(props) {
  return (
    <button onClick={props.onClick} style={{
      background:"transparent",color:"#F0EAD6",fontFamily:"'Jost',sans-serif",
      fontSize:".82rem",padding:".75rem 1.75rem",
      border:"1px solid #2A2520",cursor:"pointer"
    }}>
      {props.children}
    </button>
  );
}
