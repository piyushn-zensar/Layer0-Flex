"use client";
// API client for the FastAPI backend (proxied at /api).  Owner: Piyush.
import { useCallback, useEffect, useState } from "react";

const DEFAULT_ACTOR = "Bid Manager";

export function currentActor(): string {
  if (typeof document === "undefined") return DEFAULT_ACTOR;
  const m = document.cookie.match(/(?:^|; )actor=([^;]*)/);
  return m ? decodeURIComponent(m[1]) : DEFAULT_ACTOR;
}

export function setActor(name: string) {
  document.cookie = `actor=${encodeURIComponent(name)}; path=/; max-age=31536000`;
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("X-Actor", encodeURIComponent(currentActor())); // the backend records who acted
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const res = await fetch(path, { ...init, headers, cache: "no-store" });
  if (!res.ok) throw new Error(await errorText(res));
  return res.json() as Promise<T>;
}

/** The API's own message ({"detail": ...}), not raw JSON. */
async function errorText(res: Response): Promise<string> {
  const body = await res.text();
  try {
    const d = JSON.parse(body).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.map((e) => e.msg ?? String(e)).join("; ");
  } catch { /* not JSON */ }
  return `Request failed (${res.status})${body ? `: ${body.slice(0, 200)}` : ""}`;
}

export function post<T = unknown>(path: string, body?: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body ?? {}) });
}

/** Fetch on mount; call reload() after an action. */
export function useApi<T>(path: string) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<string>();
  const reload = useCallback(() => api<T>(path).then((d) => { setData(d); setError(undefined); },
    (e) => setError(e instanceof Error ? e.message : String(e))), [path]);
  useEffect(() => {
    reload();
  }, [reload]);
  return { data, error, reload };
}
