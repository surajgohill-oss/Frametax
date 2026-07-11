import { useEffect, useRef, useState } from "react";
import { useAppState } from "../state/AppState";
import { Money, humanizeToken } from "../lib/format";

function isTypingTarget(el) {
  if (!el) return false;
  const tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || el.isContentEditable;
}

// optimizer_value is an impact-priority rating ("high"/"medium"/"low"),
// not a dollar figure — labeled explicitly so it never reads as a bare,
// unexplained enum value next to the money column.
function priorityBadgeClass(value) {
  switch (value) {
    case "high": return "amber";
    case "medium": return "silver";
    case "low": return "charcoal";
    default: return "charcoal";
  }
}

// Real status fields (MissingInput.blocking, GreyAreaItem.status) mapped
// onto the plain-language workflow states a producer actually cares
// about — never a raw enum value.
function questionState(isGreyArea, data) {
  if (isGreyArea) return { label: "Decision required", cls: "amber" };
  return data.blocking ? { label: "Decision required", cls: "red" } : { label: "Unresolved", cls: "silver" };
}

/**
 * Unifies the two real kinds of open question this backend produces —
 * MissingInput (Question Engine, from /package) and open GreyAreaItem
 * (Legal Engine, from /legal) — into one workflow list. Nothing here is
 * fabricated: every field rendered is a real backend field.
 */
export default function QuestionStack({ missingInputs = [], greyAreas = [] }) {
  const items = [
    ...missingInputs.map((m) => ({ id: m.identifier, kind: "question", data: m })),
    ...greyAreas.filter((g) => g.status === "open").map((g) => ({ id: g.item_id, kind: "question", data: g })),
  ];
  const [activeIndex, setActiveIndex] = useState(items.length > 0 ? 0 : -1);
  const { openInspector } = useAppState();
  const listRef = useRef(null);

  useEffect(() => {
    function handleKey(e) {
      if (isTypingTarget(document.activeElement)) {
        if (e.key === "Escape") document.activeElement.blur();
        return;
      }
      if (e.key === "j" || e.key === "J") {
        setActiveIndex((i) => Math.min(items.length - 1, i + 1));
      } else if (e.key === "k" || e.key === "K") {
        setActiveIndex((i) => Math.max(0, i - 1));
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [items.length]);

  if (items.length === 0) {
    return <p className="empty-state">No open questions — every account is either qualified or has a resolved position.</p>;
  }

  const isGreyArea = (data) => "authority_to_ask" in data;

  return (
    <div className="row-list" ref={listRef}>
      {items.map((item, i) => {
        const grey = isGreyArea(item.data);
        const state = questionState(grey, item.data);
        return (
          <div
            key={item.id}
            className={`row-item question-row ${i === activeIndex ? "active" : ""}`}
            onClick={() => {
              setActiveIndex(i);
              openInspector("question", item.data);
            }}
          >
            <div className="row-main">
              <div className="row-title">{grey ? item.data.resolving_evidence : item.data.question}</div>
              <div className="question-status-row">
                <span className={`badge ${state.cls}`}>{state.label}</span>
                {grey && item.data.account_codes?.length > 0 && (
                  <span className="text-tertiary small mono">accounts {item.data.account_codes.join(", ")}</span>
                )}
                <span className="text-tertiary small">
                  {grey
                    ? `${item.data.authority_to_ask} · ${item.data.jurisdiction_code}`
                    : `Affects ${(item.data.downstream_engines || []).map(humanizeToken).join(", ")}`}
                </span>
              </div>
            </div>
            <div className="row-value">
              {grey
                ? <Money value={item.data.amount_usd} />
                : <span className={`badge ${priorityBadgeClass(item.data.optimizer_value)}`}>{item.data.optimizer_value} priority</span>}
            </div>
          </div>
        );
      })}
      <p className="text-tertiary small" style={{ marginTop: 8 }}>J / K to move between questions · click to inspect</p>
    </div>
  );
}
