const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  events: {
    list: () => req<any[]>("/events/"),
    get: (id: number) => req<any>(`/events/${id}`),
    create: (d: any) => req<any>("/events/", { method: "POST", body: JSON.stringify(d) }),
    update: (id: number, d: any) => req<any>(`/events/${id}`, { method: "PATCH", body: JSON.stringify(d) }),
    delete: (id: number) => req<void>(`/events/${id}`, { method: "DELETE" }),
  },
  venues: {
    list: () => req<any[]>("/venues/"),
    get: (slug: string) => req<any>(`/venues/${slug}`),
    sections: (slug?: string) => slug ? req<any[]>(`/venues/${slug}/sections`) : Promise.resolve([]),
  },
  listings: {
    byEvent: (id: number, mp?: string) => req<any[]>(`/listings/events/${id}${mp ? `?marketplace=${mp}` : ""}`),
  },
  analytics: {
    summary: () => req<any>("/analytics/summary"),
    eventSummary: (id: number, mp?: string) => req<any[]>(`/analytics/events/${id}/summary${mp ? `?marketplace=${mp}` : ""}`),
    priceHistory: (id: number, hours = 168, mp?: string) => req<any[]>(`/analytics/events/${id}/price-history?hours=${hours}${mp ? `&marketplace=${mp}` : ""}`),
    heatmap: (id: number) => req<any[]>(`/analytics/events/${id}/heatmap`),
    compare: (id: number) => req<any[]>(`/analytics/events/${id}/compare`),
  },
  poll: {
    trigger: (id: number) => req<any>(`/poll/events/${id}/trigger`, { method: "POST" }),
    runs: (id: number) => req<any[]>(`/poll/events/${id}/runs`),
  },
  debug: {
    errors: (mp?: string, type?: string) => req<any[]>(`/debug/errors?limit=100${mp ? `&marketplace=${mp}` : ""}${type ? `&error_type=${type}` : ""}`),
    errorSummary: () => req<any[]>("/debug/errors/summary"),
    memory: (mp?: string) => req<any[]>(`/debug/memory${mp ? `?marketplace=${mp}` : ""}`),
    deleteMemory: (id: number) => req<void>(`/debug/memory/${id}`, { method: "DELETE" }),
    clearMemory: (mp?: string) => req<void>(`/debug/memory${mp ? `?marketplace=${mp}` : ""}`, { method: "DELETE" }),
    testCollect: (marketplace: string, url: string) =>
      req<any>("/debug/test-collect", { method: "POST", body: JSON.stringify({ marketplace, url }) }),
  },
};
