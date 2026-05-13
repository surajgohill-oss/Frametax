"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";

const VENUES = [
  { value: "hollywood_bowl", label: "Hollywood Bowl" },
  { value: "kia_forum", label: "Kia Forum" },
  { value: "crypto_arena", label: "Crypto.com Arena" },
  { value: "greek_theatre", label: "Greek Theatre" },
  { value: "sofi_stadium", label: "SoFi Stadium" },
];

export default function NewEventPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: "",
    venue_slug: "hollywood_bowl",
    event_date: "",
    stubhub_url: "",
    seatgeek_url: "",
    poll_interval_minutes: 60,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title.trim() || !form.event_date) {
      setError("Title and date are required.");
      return;
    }
    if (!form.stubhub_url && !form.seatgeek_url) {
      setError("At least one marketplace URL is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const ev = await api.events.create({
        ...form,
        poll_interval_minutes: Number(form.poll_interval_minutes),
      });
      router.push(`/events/${ev.id}`);
    } catch (err: any) {
      setError(err?.message ?? "Failed to create event.");
      setSaving(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Add Event</h1>
        <p className="text-slate-400 text-sm mt-1">Track ticket prices for a new concert</p>
      </div>

      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Event Title *</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
              placeholder="e.g. Taylor Swift – The Eras Tour"
              className="w-full px-3 py-2 bg-[#0d1117] border border-[#2a3145] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 placeholder:text-slate-600"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Venue *</label>
              <select
                value={form.venue_slug}
                onChange={(e) => set("venue_slug", e.target.value)}
                className="w-full px-3 py-2 bg-[#0d1117] border border-[#2a3145] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              >
                {VENUES.map((v) => (
                  <option key={v.value} value={v.value}>{v.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Event Date *</label>
              <input
                type="date"
                value={form.event_date}
                onChange={(e) => set("event_date", e.target.value)}
                className="w-full px-3 py-2 bg-[#0d1117] border border-[#2a3145] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">StubHub URL</label>
            <input
              type="url"
              value={form.stubhub_url}
              onChange={(e) => set("stubhub_url", e.target.value)}
              placeholder="https://www.stubhub.com/..."
              className="w-full px-3 py-2 bg-[#0d1117] border border-[#2a3145] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 placeholder:text-slate-600"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">SeatGeek URL</label>
            <input
              type="url"
              value={form.seatgeek_url}
              onChange={(e) => set("seatgeek_url", e.target.value)}
              placeholder="https://seatgeek.com/..."
              className="w-full px-3 py-2 bg-[#0d1117] border border-[#2a3145] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 placeholder:text-slate-600"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Poll Interval (minutes)
            </label>
            <input
              type="number"
              min={15}
              max={1440}
              value={form.poll_interval_minutes}
              onChange={(e) => set("poll_interval_minutes", e.target.value)}
              className="w-full px-3 py-2 bg-[#0d1117] border border-[#2a3145] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-500 mt-1">Minimum 15, default 60</p>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
            >
              {saving ? "Adding…" : "Add to Watchlist"}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-4 py-2 border border-[#2a3145] text-slate-300 text-sm rounded-lg hover:bg-[#1e2535] transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}
