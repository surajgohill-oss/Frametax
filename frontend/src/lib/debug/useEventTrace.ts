"use client";
import { useEffect } from "react";

export function useEventTrace(events: any[]) {
  useEffect(() => {
    if (process.env.NODE_ENV !== "development") return;
    const traces = events.map((e) => ({
      id: e.id,
      canonical_id: e.canonical_id,
      tracked_event_count: e.lineage?.tracked_event_count ?? e.tracked_events?.length ?? 0,
      marketplaces: e.lineage?.marketplaces ?? [],
      query_path: e.lineage?.query_path ?? [],
    }));
    (window as any).__EVENT_TRACE__ = traces;
    console.log("[EVENT_LINEAGE]", traces.length, "events", traces);
  }, [events]);
}
