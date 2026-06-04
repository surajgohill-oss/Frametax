"use client";
import { useState, useEffect, useCallback } from "react";

const KEY = "my_events";

export function useMyEvents() {
  const [myEvents, setMyEvents] = useState<Set<number>>(new Set());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setMyEvents(new Set(JSON.parse(raw) as number[]));
    } catch {}
  }, []);

  const toggle = useCallback((id: number) => {
    setMyEvents((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch {}
      return next;
    });
  }, []);

  return { myEvents, toggle, mounted };
}
