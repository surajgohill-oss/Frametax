"use client";
import { useState, useEffect } from "react";

const KEY = "followed_events";

export function useFollowed() {
  const [followed, setFollowed] = useState<Set<number>>(new Set());

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setFollowed(new Set(JSON.parse(raw) as number[]));
    } catch {}
  }, []);

  function toggle(id: number) {
    setFollowed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      try { localStorage.setItem(KEY, JSON.stringify([...next])); } catch {}
      return next;
    });
  }

  return { followed, toggle };
}
