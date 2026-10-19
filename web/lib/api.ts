"use client";
// API client for the FastAPI backend (proxied at /api), and sign-in.  Owner: Piyush.
import { useCallback, useEffect, useState } from "react";

export const LOGIN = "/login";
export const SIGNUP = "/signup";
/** sessionStorage key for the demo password typed on the sign-in page, so the walkthrough can switch roles. */
const DEMO_PASSWORD_KEY = "layer0.demo-password";

/** Every request carries the HttpOnly layer0_token cookie (the /api proxy is same-origin). A 401 means no valid
 * token: the browser goes to the sign-in page and comes back to this page afterwards. */
export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const res = await fetch(path, { ...init, headers, cache: "no-store", credentials: "same-origin" });
  if (res.status === 401 && !path.startsWith("/api/auth/") && typeof location !== "undefined" && ![LOGIN, SIGNUP].includes(location.pathname)) {
    location.assign(`${LOGIN}?next=${encodeURIComponent(location.pathname + location.search)}`);
  }
  if (!res.ok) throw new Error(await errorText(res));
  return res.json() as Promise<T>;
}

/** The signed-in user: GET /api/auth/me (the token's claims plus role_label). */
export interface Me { sub: string; name: string; role: string; role_label: string; bu: string | null; exp: number }

/** POST /api/auth/login; the API sets the cookie. Keeps the password for this tab only (demo accounts share it). */
export async function signIn(username: string, password: string): Promise<Me> {
  const { user } = await post<{ user: Me }>("/api/auth/login", { username, password });
  // ponytail: the PoC's one shared demo password, kept per tab so the walkthrough can sign in as another role
  try { sessionStorage.setItem(DEMO_PASSWORD_KEY, password); } catch { /* storage blocked */ }
  return user;
}

/** POST /api/auth/signup (P-31): creates the account with the role the person chose and signs it in (the API sets
 * the cookie). The administrator cannot be chosen. */
export interface SignUp { username: string; name: string; password: string; role: string; bu: string | null }
export async function signUp(body: SignUp): Promise<Me> {
  const { user } = await post<{ user: Me }>("/api/auth/signup", body);
  return user;
}

/** Sign in as another demo account with the password typed on the sign-in page (asks again if it is not known). */
export async function signInAs(username: string): Promise<Me> {
  let password: string | null = null;
  try { password = sessionStorage.getItem(DEMO_PASSWORD_KEY); } catch { /* storage blocked */ }
  password ??= window.prompt(`Password to sign in as ${username}`);
  if (!password) throw new Error("Sign-in cancelled.");
  return signIn(username, password);
}

export async function signOut(): Promise<void> {
  try { sessionStorage.removeItem(DEMO_PASSWORD_KEY); } catch { /* storage blocked */ }
  await post("/api/auth/logout");
  location.assign(LOGIN);
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

/** One line for a toast or an inline alert from whatever a request rejected with: the API's detail, never "Error: …". */
export function errorMessage(e: unknown, fallback = "Something went wrong. Please try again."): string {
  const text = e instanceof Error ? e.message : typeof e === "string" ? e : "";
  return text.replace(/^Error:\s*/, "").replace(/^\d{3}:\s*/, "").trim() || fallback;
}

export function post<T = unknown>(path: string, body?: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body ?? {}) });
}

/** Bid-manager-only actions (technical-architecture section 16.6); the API checks too, this only greys the button. */
export const isBidManager = (me?: Me) => me?.role === "bid_manager";
/** The administrator reads only (the API answers 403 to its writes): write buttons are greyed for it (19 Oct review). */
export const isReader = (me?: Me) => me?.role === "admin";
export const BID_MANAGER_ONLY = "Only the bid manager can do this.";

/** The signed-in user (undefined while loading). */
// One lookup per page load, shared by every component that asks (a role check per table row costs no request);
// signing in and out reload the page, so it never shows the previous person.
let signedIn: Promise<Me> | undefined;
export function useMe(): Me | undefined {
  const [me, setMe] = useState<Me>();
  useEffect(() => {
    let live = true;
    (signedIn ??= api<Me>("/api/auth/me").catch((e) => { signedIn = undefined; throw e; }))
      .then((m) => { if (live) setMe(m); }, () => { /* not signed in: the page guard and the API handle it */ });
    return () => { live = false; };
  }, []);
  return me;
}

/** Fetch on mount; call reload() after an action. */
export function useApi<T>(path: string) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<string>();
  const reload = useCallback(() => api<T>(path).then((d) => { setData(d); setError(undefined); },
    (e) => setError(e instanceof Error ? e.message : String(e))), [path]);
  useEffect(() => {
    reload();
    // A page left open in another tab (or restored by Back) would show old data, e.g. "not frozen" after a freeze
    // made elsewhere: fetch again whenever the tab comes back into view.
    const onFocus = () => { if (document.visibilityState === "visible") reload(); };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onFocus);
    return () => { window.removeEventListener("focus", onFocus); document.removeEventListener("visibilitychange", onFocus); };
  }, [reload]);
  return { data, error, reload };
}
