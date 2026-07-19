import { useEffect, useRef, useState } from "react";
import { useAppState } from "../state/AppState";

function isTypingTarget(el) {
  if (!el) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || el.isContentEditable;
}

/**
 * Unifies the two real kinds of open question this backend produces —
 * MissingInput (Question Engine, from /package) and open GreyAreaItem
 * (Legal Engine, from /legal) — into one workflow list.
 *
 * Presentation is the approved artifact question card (.qcard): a
 * money-first swing figure, then the question, then a jurisdiction/authority
 * meta row. Money-bearing items are "hot" (amber rule). Nothing is
 * fabricated — every field rendered is a real backend field, and the
 * j/k keyboard navigation plus the Inspector wiring are unchanged.
 */
export default function QuestionStack({ missingInputs = [], greyAreas = [], sortByMoney = true }) {
  // Money-bearing grey areas lead — they are what gates optimization.
  // sortByMoney is the artifact's "by $ ▾" ordering: dollar swing
  // descending; off = the natural stack order (greys first, then inputs).
  const items = [
    ...greyAreas.filter((g) => g.status === "open").map((g) => ({ id: g.item_id, data: g, grey: true })),
    ...missingInputs.map((m) => ({ id: m.identifier, data: m, grey: false })),
  ];
  if (sortByMoney) {
    items.sort((a, b) => ((b.grey ? b.data.amount_usd || 0 : 0) - (a.grey ? a.data.amount_usd || 0 : 0)));
  }
  const [activeIndex, setActiveIndex] = useState(items.length > 0 ? 0 : -1);
  const { openInspector } = useAppState();
  const listRef = useRef(null);

  useEffect(() => {
    function handleKey(e) {
      if (isTypingTarget(document.activeElement)) {
        if (e.key === "Escape") document.activeElement.blur();
        return;
      }
      if (e.key === "j" || e.key === "J") setActiveIndex((i) => Math.min(items.length - 1, i + 1));
      else if (e.key === "k" || e.key === "K") setActiveIndex((i) => Math.max(0, i - 1));
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [items.length]);

  if (items.length === 0) {
    return <p className="qs-empty">No open questions — every account is either qualified or has a resolved position.</p>;
  }

  return (
    <div ref={listRef}>
      {items.map((item, i) => {
        const d = item.data;
        // Swing column: real money for grey areas, priority rating otherwise.
        const swing = item.grey
          ? `±$${Math.round(d.amount_usd || 0).toLocaleString()}`
          : (d.optimizer_value || "—");
        const title = item.grey ? d.resolving_evidence : d.question;
        // Artifact status vocabulary: "awaiting" for anything unresolved.
        // No deadline data is served, so "overdue" is never fabricated;
        // the red emphasis (.age) marks money-bearing/blocking items.
        const left = item.grey ? `${d.jurisdiction_code} · ${d.authority_to_ask}` : "Question engine";
        const right = "awaiting";
        return (
          <div
            key={item.id}
            className={`qcard${item.grey ? " hot" : ""}${i === activeIndex ? " sel" : ""}`}
            onClick={() => { setActiveIndex(i); openInspector("question", d); }}
          >
            <div className="sw">{swing}</div>
            <div className="qt"><b>Q{i + 1}</b> · {title}</div>
            <div className="meta">
              <span>{left}</span>
              <span className={item.grey ? "age" : ""}>{right}</span>
            </div>
          </div>
        );
      })}
      <p className="qs-hint">J / K to move · click to inspect</p>
    </div>
  );
}
