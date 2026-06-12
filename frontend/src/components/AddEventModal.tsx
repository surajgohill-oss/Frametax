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

// Venues list matching Railway DB slugs
const VENUE_OPTIONS = [
  { slug: "sofi-stadium",    label: "SoFi Stadium" },
  { slug: "crypto-arena",    label: "Crypto.com Arena" },
  { slug: "kia-forum",       label: "Kia Forum" },
  { slug: "hollywood-bowl",  label: "Hollywood Bowl" },
  { slug: "greek-theatre",   label: "Greek Theatre LA" },
  { slug: "oakland-arena",   label: "Oakland Arena" },
];

// Needs manual form (not auto-created from URL)
const MANUAL_MARKETPLACES: MarketplaceSlug[] = ["gametime", "tickpick", "vividseats"];

export default function AddEventModal({ onClose }: Props) {
  const [url, setUrl] = useState("");
  const [detected, setDetected] = useState<MarketplaceSlug | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [createdId, setCreatedId] = useState<number | null>(null);

  // Manual form fields (used for non-StubHub/SeatGeek)
  const [manualTitle, setManualTitle] = useState("");
  const [manualArtist, setManualArtist] = useState("");
  const [manualVenue, setManualVenue] = useState("");
  const [manualDate, setManualDate] = useState("");

  const handleUrlChange = (v: string) => {
    setUrl(v);
    setDetected(detectMarketplace(v));
    setState("idle");
  };

  const isManual = detected !== null && MANUAL_MARKETPLACES.includes(detected);
  const canSubmitAuto = detected !== null && !isManual && url.trim().length > 10;
  const canSubmitManual = isManual && url.trim().length > 10 && manualTitle.trim() && manualVenue && manualDate;
  const canSubmit = canSubmitAuto || canSubmitManual;

  const submit = async () => {
    if (!canSubmit) return;
    setState("loading");
    setErrorMsg("");

    try {
      let result: { id?: number; event_id?: number; detail?: string };

      if (detected === "stubhub" || detected === "seatgeek") {
        // Primary create — backend auto-fetches event details from URL
        const body = detected === "stubhub"
          ? { stubhub_url: url }
          : { seatgeek_url: url };
        result = await api.events.create(body);
      } else if (isManual) {
        // Manual creation via bypass endpoint (for VividSeats, Gametime, TickPick)
        const mpUrls: Record<string, string> = {};
        mpUrls[detected!] = url;
        result = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL ?? "https://backend-production-509f.up.railway.app"}/api/debug/create-event-bypass-freeze`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              title: manualTitle.trim(),
              artist: manualArtist.trim() || manualTitle.trim(),
              venue_slug: manualVenue,
              event_date: new Date(manualDate).toISOString(),
              marketplace_urls: mpUrls,
            }),
          }
        ).then((r) => r.json());
      } else {
        setState("error");
        setErrorMsg("Unsupported marketplace. Use StubHub, SeatGeek, Vivid Seats, Gametime, or TickPick.");
        return;
      }

      if (result?.detail && typeof result.detail === "string" && result.detail.includes("error")) {
        setState("error");
        setErrorMsg(result.detail);
        return;
      }
      if ((result as { error?: string }).error) {
        setState("error");
        setErrorMsg((result as { error?: string }).error!);
        return;
      }

      const id = result?.id ?? result?.event_id ?? (result as { event_id?: number }).event_id;
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
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#141820] shadow-2xl max-h-[90vh] overflow-y-auto">
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
                onClick={() => { setUrl(""); setDetected(null); setState("idle"); setCreatedId(null); setManualTitle(""); setManualArtist(""); setManualVenue(""); setManualDate(""); }}
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
              Paste a marketplace event URL to start tracking ticket data.
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
                  onKeyDown={(e) => e.key === "Enter" && !isManual && submit()}
                />
              </div>

              {/* Detected marketplace */}
              {detected && (
                <p className={`text-xs font-medium ${MP_COLORS[detected]}`}>
                  ✓ {MP_LABELS[detected]} URL detected
                  {isManual && " — fill in event details below"}
                </p>
              )}
              {url && !detected && (
                <p className="text-xs text-slate-600">
                  Supported: StubHub, SeatGeek, Gametime, TickPick, Vivid Seats
                </p>
              )}
            </div>

            {/* Manual fields — shown for VividSeats / Gametime / TickPick */}
            {isManual && (
              <div className="space-y-3 rounded-xl border border-white/8 bg-white/2 p-3">
                <p className="text-[10px] text-slate-500 uppercase tracking-wide font-semibold">Event Details</p>
                <div className="space-y-2">
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">Event Title *</label>
                    <input
                      type="text"
                      placeholder="e.g. Kid Cudi"
                      value={manualTitle}
                      onChange={(e) => setManualTitle(e.target.value)}
                      className="w-full bg-black/30 border border-white/8 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-white/20"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">Artist (optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. Kid Cudi"
                      value={manualArtist}
                      onChange={(e) => setManualArtist(e.target.value)}
                      className="w-full bg-black/30 border border-white/8 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-white/20"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">Venue *</label>
                    <select
                      value={manualVenue}
                      onChange={(e) => setManualVenue(e.target.value)}
                      className="w-full bg-black/30 border border-white/8 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/20"
                    >
                      <option value="">Select venue…</option>
                      {VENUE_OPTIONS.map((v) => (
                        <option key={v.slug} value={v.slug}>{v.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">Event Date *</label>
                    <input
                      type="date"
                      value={manualDate}
                      onChange={(e) => setManualDate(e.target.value)}
                      className="w-full bg-black/30 border border-white/8 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/20"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {state === "error" && errorMsg && (
              <div className="flex gap-2 bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                <AlertCircle size={14} className="text-red-400 mt-0.5 shrink-0" />
                <p className="text-xs text-red-300">{errorMsg}</p>
              </div>
            )}

            {/* Supported marketplaces info */}
            {!isManual && (
              <div className="bg-white/3 rounded-lg p-3 space-y-1.5">
                <p className="text-[10px] text-slate-500 uppercase tracking-wide font-medium">Auto-create from URL</p>
                <div className="flex flex-wrap gap-1.5">
                  {(["stubhub", "seatgeek", "vividseats", "gametime", "tickpick"] as MarketplaceSlug[]).map((mp) => (
                    <span key={mp} className={`text-xs font-medium ${MP_COLORS[mp]} bg-white/4 rounded px-2 py-0.5`}>
                      {MP_LABELS[mp]}
                    </span>
                  ))}
                </div>
                <p className="text-[10px] text-slate-700 mt-1">StubHub & SeatGeek auto-fill details. Others require manual entry.</p>
              </div>
            )}

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
