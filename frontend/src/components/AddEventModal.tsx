"use client";

import { useState } from "react";
import { X, Link2, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

interface Props {
  onClose: () => void;
}

type MarketplaceSlug = "stubhub" | "seatgeek" | "gametime" | "tickpick" | "vividseats";

function detectMarketplace(url: string): MarketplaceSlug | null {
  if (!url) return null;
  if (url.includes("stubhub.com")) return "stubhub";
  if (url.includes("seatgeek.com")) return "seatgeek";
  if (url.includes("gametime.co")) return "gametime";
  if (url.includes("tickpick.com")) return "tickpick";
  if (url.includes("vividseats.com")) return "vividseats";
  return null;
}

const MP_LABELS: Record<MarketplaceSlug, string> = {
  stubhub: "StubHub",
  seatgeek: "SeatGeek",
  gametime: "Gametime",
  tickpick: "TickPick",
  vividseats: "Vivid Seats",
};

const MP_COLORS: Record<MarketplaceSlug, string> = {
  stubhub: "text-blue-400",
  seatgeek: "text-green-400",
  gametime: "text-orange-400",
  tickpick: "text-purple-400",
  vividseats: "text-red-400",
};

export default function AddEventModal({ onClose }: Props) {
  const [url, setUrl] = useState("");
  const [detected, setDetected] = useState<MarketplaceSlug | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [createdId, setCreatedId] = useState<number | null>(null);

  const handleUrlChange = (v: string) => {
    setUrl(v);
    setDetected(detectMarketplace(v));
    setState("idle");
  };

  const canSubmit = detected !== null && url.trim().length > 10;

  const submit = async () => {
    if (!canSubmit) return;
    setState("loading");
    setErrorMsg("");

    try {
      let result: { id?: number; event_id?: number; detail?: string };

      if (detected === "stubhub" || detected === "seatgeek") {
        // Primary create — backend auto-fetches event details
        const body = detected === "stubhub"
          ? { stubhub_url: url }
          : { seatgeek_url: url };
        result = await api.events.create(body);
      } else {
        // For other marketplaces: not yet auto-created from URL alone
        // Show a friendly message about what's supported
        setState("error");
        setErrorMsg(
          `Auto-creation from ${MP_LABELS[detected!]} URLs isn't supported yet. Supported: StubHub, SeatGeek. Use a StubHub/SeatGeek URL, or add the event manually then track additional marketplaces from the event page.`
        );
        return;
      }

      if (result?.detail) {
        setState("error");
        setErrorMsg(result.detail);
        return;
      }

      const id = result?.id ?? result?.event_id;
      if (!id) {
        setState("error");
        setErrorMsg("Event created but no ID returned. Refresh the dashboard.");
        return;
      }

      setCreatedId(id);
      setState("success");
    } catch (e) {
      setState("error");
      setErrorMsg(e instanceof Error ? e.message : "Unexpected error");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#141820] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/6">
          <h2 className="text-sm font-semibold text-white">Add Event</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X size={16} />
          </button>
        </div>

        {state === "success" ? (
          /* Success state */
          <div className="px-5 py-8 flex flex-col items-center gap-3 text-center">
            <CheckCircle2 size={32} className="text-emerald-400" />
            <p className="text-sm font-medium text-white">Event added successfully</p>
            <p className="text-xs text-slate-500">
              The event is now being tracked. Data will appear within the next collection cycle.
            </p>
            <div className="flex gap-2 mt-2">
              <a
                href={`/events/${createdId}`}
                className="text-xs font-medium text-white bg-blue-500/20 hover:bg-blue-500/30 border border-blue-400/20 rounded-lg px-4 py-2 transition-all"
              >
                View Event →
              </a>
              <button
                onClick={() => { setUrl(""); setDetected(null); setState("idle"); setCreatedId(null); }}
                className="text-xs text-slate-400 hover:text-white px-4 py-2 rounded-lg transition-all hover:bg-white/5"
              >
                Add Another
              </button>
            </div>
          </div>
        ) : (
          /* Input state */
          <div className="px-5 py-4 space-y-4">
            <p className="text-xs text-slate-500">
              Paste a marketplace event URL and Concert Tracker will start collecting ticket data for it.
            </p>

            {/* URL input */}
            <div className="space-y-2">
              <label className="text-xs text-slate-400 font-medium">Event URL</label>
              <div className="relative">
                <Link2 size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
                <input
                  type="url"
                  placeholder="https://www.stubhub.com/event/..."
                  value={url}
                  onChange={(e) => handleUrlChange(e.target.value)}
                  className="w-full bg-black/30 border border-white/8 rounded-lg pl-8 pr-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-white/20 transition-colors"
                  autoFocus
                  onKeyDown={(e) => e.key === "Enter" && submit()}
                />
              </div>

              {/* Detected marketplace */}
              {detected && (
                <p className={`text-xs font-medium ${MP_COLORS[detected]}`}>
                  ✓ {MP_LABELS[detected]} URL detected
                </p>
              )}
              {url && !detected && (
                <p className="text-xs text-slate-600">
                  Supported: StubHub, SeatGeek, Gametime, TickPick, Vivid Seats
                </p>
              )}
            </div>

            {/* Error */}
            {state === "error" && errorMsg && (
              <div className="flex gap-2 bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                <AlertCircle size={14} className="text-red-400 mt-0.5 shrink-0" />
                <p className="text-xs text-red-300">{errorMsg}</p>
              </div>
            )}

            {/* Supported marketplaces info */}
            <div className="bg-white/3 rounded-lg p-3 space-y-1.5">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide font-medium">Supported at creation</p>
              <div className="flex flex-wrap gap-1.5">
                {(["stubhub", "seatgeek"] as MarketplaceSlug[]).map((mp) => (
                  <span key={mp} className={`text-xs font-medium ${MP_COLORS[mp]} bg-white/4 rounded px-2 py-0.5`}>
                    {MP_LABELS[mp]}
                  </span>
                ))}
                <span className="text-xs text-slate-600 bg-white/4 rounded px-2 py-0.5">+3 via event page</span>
              </div>
            </div>

            {/* Submit */}
            <button
              onClick={submit}
              disabled={!canSubmit || state === "loading"}
              className="w-full flex items-center justify-center gap-2 text-sm font-medium text-white bg-blue-500/20 hover:bg-blue-500/30 border border-blue-400/20 rounded-lg py-2.5 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {state === "loading" ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Adding event…
                </>
              ) : (
                "Add Event"
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
