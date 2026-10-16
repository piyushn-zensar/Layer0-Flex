"use client";
// Sign-in (technical-architecture section 16.6).  Owner: Piyush.
// Covers the shell, so nothing behind it asks the API before there is a token. After sign-in the browser goes back
// to ?next= (set by lib/api.ts on a 401), else the portfolio; a full load so every page fetches as the new user.
import { useEffect, useState } from "react";
import { errorMessage, signIn } from "@/lib/api";
import { Alert, Busy } from "@/components/ui";

export default function LoginPage() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>();
  const [search, setSearch] = useState(""); // ?next= carried over to the sign-up link (read after mount: no hydration mismatch)
  useEffect(() => setSearch(location.search), []);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true); setMessage(undefined);
    try {
      await signIn(String(form.get("username") ?? "").trim(), String(form.get("password") ?? ""));
      const next = new URLSearchParams(location.search).get("next");
      location.assign(next?.startsWith("/") && !next.startsWith("//") ? next : "/portfolio");
    } catch (err) { setMessage(errorMessage(err)); setBusy(false); }
  }
  return (
    <div className="login">
      <form className="card form compact" onSubmit={submit} aria-busy={busy}>
        <h1><span className="brand-mark" aria-hidden>L0</span> Sign in to Layer 0</h1>
        <label>Username <input name="username" required autoComplete="username" autoFocus placeholder="e.g. bid.manager or crown.pm" disabled={busy} /></label>
        <label>Password <input name="password" type="password" required autoComplete="current-password" disabled={busy} /></label>
        <button disabled={busy}>Sign in</button>
        {busy && <Busy label="Signing in…" />}
        <Alert kind="error">{message}</Alert>
        <p className="muted">No account yet? <a href={`/signup${search}`}>Sign up</a></p>
      </form>
    </div>
  );
}
