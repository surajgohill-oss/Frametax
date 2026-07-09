"use client";
import { useState, useEffect, useCallback } from "react";

const KEY = "awr_archived";

function load(): Set<number> {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? new Set(JSON.parse(raw) as number[]) : new Set();
  } catch { return new Set(); }
}

function save(ids: Set<number>) {
  try { localStorage.setItem(KEY, JSON.stringify([...ids])); } catch {}
}

export function useArchivedEvents() {
  const [archivedEvents, setArchivedEvents] = useState<Set<number>>(new Set());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setArchivedEvents(load());
    setMounted(true);
  }, []);

  const archive = useCallback((id: number) => {
    setArchivedEvents(prev => {
      const next = new Set(prev);
      next.add(id);
      save(next);
      return next;
    });
  }, []);

  const unarchive = useCallback((id: number) => {
    setArchivedEvents(prev => {
      const next = new Set(prev);
      next.delete(id);
      save(next);
      return next;
    });
  }, []);

  const toggle = useCallback((id: number) => {
    setArchivedEvents(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      save(next);
      return next;
    });
  }, []);

  return { archivedEvents, archive, unarchive, toggle, mounted };
}
