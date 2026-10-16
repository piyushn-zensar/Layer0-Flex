"use client";
// Sign-up (P-31, C-26): username, display name, password and the role the person chooses (bid manager, unit manager,
// unit designer / engineer; never administrator), with a unit for the unit roles. Signs the new account in and goes
// back to ?next=, else the portfolio. Choosing one's own role is a known proof-of-concept limit.  Owner: Piyush.
import { useEffect, useState } from "react";
import { api, errorMessage, signUp } from "@/lib/api";
import { ROLE_LABELS } from "@/lib/types";
import { Alert, Busy } from "@/components/ui";

const ROLES = ["bid_manager", "product_manager", "design_engineer"]; // administrator: seeded by the server only
const MIN_PASSWORD = 10;

export default function SignUpPage() {
  const [units, setUnits] = useState<{ code: string; name: string }[]>([]);
  const [role, setRole] = useState("design_engineer");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>();
  const [search, setSearch] = useState(""); // ?next= carried back to the sign-in link (read after mount)
  useEffect(() => { setSearch(location.search); api<{ code: string; name: string }[]>("/api/auth/units").then(setUnits, (e) => setMessage(errorMessage(e))); }, []);
  const unitRole = role !== "bid_manager";

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true); setMessage(undefined);
    try {
      await signUp({ username: String(f.get("username") ?? "").trim(), name: String(f.get("name") ?? "").trim(),
        password: String(f.get("password") ?? ""), role, bu: unitRole ? String(f.get("bu") ?? "") : null });
      const next = new URLSearchParams(location.search).get("next");
      location.assign(next?.startsWith("/") && !next.startsWith("//") ? next : "/portfolio");
    } catch (err) { setMessage(errorMessage(err)); setBusy(false); }
  }
  return (
    <div className="login">
      <form className="card form compact" onSubmit={submit} aria-busy={busy}>
        <h1><span className="brand-mark" aria-hidden>L0</span> Sign up for Layer 0</h1>
        <label>Username <input name="username" required minLength={3} maxLength={64} autoComplete="username" autoFocus placeholder="e.g. jane.doe" disabled={busy} /></label>
        <label>Display name <input name="name" required maxLength={128} autoComplete="name" placeholder="Shown on every record you make" disabled={busy} /></label>
        <label>Password <input name="password" type="password" required minLength={MIN_PASSWORD} autoComplete="new-password" placeholder={`At least ${MIN_PASSWORD} characters`} disabled={busy} /></label>
        <label>Role
          <select value={role} onChange={(e) => setRole(e.target.value)} disabled={busy}>
            {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
          </select></label>
        {unitRole && <label>Business unit
          <select name="bu" required disabled={busy || units.length === 0} defaultValue="">
            <option value="" disabled>Choose your unit</option>
            {units.map((u) => <option key={u.code} value={u.code}>{u.name}</option>)}
          </select></label>}
        <button disabled={busy}>Sign up</button>
        {busy && <Busy label="Creating the account…" />}
        <Alert kind="error">{message}</Alert>
        <p className="muted">Already have an account? <a href={`/login${search}`}>Sign in</a></p>
      </form>
    </div>
  );
}
