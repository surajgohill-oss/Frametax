import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Signal } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmt$$(n: number | null | undefined, decimals = 0): string {
  if (n == null) return "—";
  return "$" + n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export function fmtPct(n: number | null | undefined, decimals = 1): string {
  if (n == null) return "—";
  const sign = n > 0 ? "+" : "";
  return sign + n.toFixed(decimals) + "%";
}

export function fmtNum(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString("en-US");
}

export function fmtDelta(n: number | null | undefined): string {
  if (n == null) return "—";
  const sign = n > 0 ? "+" : "";
  return sign + n.toLocaleString("en-US");
}

// ── Consumer-facing signal → action ──────────────────────────────────────────

export type ActionWord = "BUY" | "WAIT" | "MONITOR";

const SIGNAL_ACTION: Record<Signal, ActionWord> = {
  deepening:    "BUY",
  capitulating: "BUY",
  loosening:    "WAIT",
  stable:       "MONITOR",
  mixed:        "MONITOR",
};

const ACTION_COLORS: Record<ActionWord, { bg: string; text: string; border: string; glow: string }> = {
  BUY:     { bg: "rgba(239,68,68,0.12)",  text: "#f87171", border: "rgba(239,68,68,0.3)",  glow: "rgba(239,68,68,0.2)" },
  WAIT:    { bg: "rgba(52,211,153,0.12)", text: "#34d399", border: "rgba(52,211,153,0.3)", glow: "rgba(52,211,153,0.2)" },
  MONITOR: { bg: "rgba(96,165,250,0.12)", text: "#60a5fa", border: "rgba(96,165,250,0.3)", glow: "rgba(96,165,250,0.2)" },
};

const SIGNAL_DESCRIPTIONS: Record<Signal, string> = {
  deepening:    "Market is tightening. Prices have been rising.",
  capitulating: "Sellers are cutting prices. Deals available now.",
  loosening:    "Prices are falling. Better deals may be ahead.",
  stable:       "Market is stable. No immediate pressure to act.",
  mixed:        "Market signals are mixed. Monitor for changes.",
};

export function signalToAction(signal: Signal | string | null | undefined): ActionWord {
  return SIGNAL_ACTION[(signal as Signal) ?? "stable"] ?? "MONITOR";
}

export function actionColors(action: ActionWord) {
  return ACTION_COLORS[action];
}

export function signalDescription(signal: Signal | string | null | undefined): string {
  return SIGNAL_DESCRIPTIONS[(signal as Signal) ?? "stable"] ?? SIGNAL_DESCRIPTIONS.stable;
}

// ── Consumer language mapping ─────────────────────────────────────────────────

export const CONSUMER_LABELS = {
  opportunity_score:   "Deal Score",
  seller_aggression:   "Seller Pressure",
  capitulation_score:  "Price Cutting Activity",
  tightness:           "Ticket Availability",
  liquidity_score:     "Coverage Score",
  churn_rate:          "Listing Turnover",
  reprice_rate:        "Pricing Activity",
  seller_confidence:   "Seller Confidence",
  velocity:            "Trading Activity",
  market_stress:       "Market Heat",
  share_of_inventory:  "Market Share",
} as const;

// ── Compact signal phrase (for card-level display) ───────────────────────────

const SIGNAL_PHRASES: Record<Signal, { text: string; dir: "up" | "down" | "flat" }> = {
  deepening:    { text: "Prices rising",  dir: "up"   },
  capitulating: { text: "Prices falling", dir: "down" },
  loosening:    { text: "Prices softening", dir: "down" },
  stable:       { text: "Market stable",  dir: "flat" },
  mixed:        { text: "Mixed signals",  dir: "flat" },
};

export function signalPhrase(signal: Signal | string | null | undefined): { text: string; dir: "up" | "down" | "flat" } {
  return SIGNAL_PHRASES[(signal as Signal) ?? "stable"] ?? SIGNAL_PHRASES.stable;
}

// ── Lifecycle context ─────────────────────────────────────────────────────────

export function lifecycleContext(
  daysOut: number | null | undefined,
  signal: Signal | string | null | undefined,
  inventoryDelta?: number | null,
): string {
  if (daysOut == null) return "";
  const d = Math.round(daysOut);
  const action = signalToAction(signal);

  if (d <= 1) {
    return action === "BUY"
      ? "Event is tomorrow. Inventory is moving fast — act now or pay more at the door."
      : "Event is tomorrow. Last-minute deals may appear in the final hours.";
  }
  if (d <= 7) {
    return action === "BUY"
      ? `${d} days out. Demand is strong. Prices typically rise sharply in the final week.`
      : `${d} days out. Some sellers are cutting prices to move remaining inventory.`;
  }
  if (d <= 14) {
    return action === "BUY"
      ? `${d} days out. The market is tightening ahead of the event.`
      : `${d} days out. Price pressure is easing — monitor for further drops.`;
  }
  if (d <= 30) {
    if (inventoryDelta != null && inventoryDelta > 200) {
      return `${d} days out. New inventory has flooded the market — unusually high supply for this stage.`;
    }
    return action === "WAIT"
      ? `${d} days out. Prices are falling with a month remaining — typical of an oversupplied market.`
      : `${d} days out. Demand is building with a month to go.`;
  }
  if (d <= 60) {
    return `${d} days out. Still in the early-to-mid market window. ${
      action === "BUY" ? "Prices trending higher than expected for this distance." :
      action === "WAIT" ? "Prices remain soft — historically good window to wait for deals." :
      "Market is stable at this stage."
    }`;
  }
  return `${d} days out. Early market — inventory remains ${
    (inventoryDelta ?? 0) > 0 ? "elevated" : "steady"
  }. Prices typically stabilize in the final 30 days.`;
}
