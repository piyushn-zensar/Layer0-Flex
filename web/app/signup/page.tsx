"use client";
// Sign-up (P-31): same card as sign-in and also covers the shell. The API creates the account and signs the person in,
// so on success the browser goes to ?next= (else the home page); a full load so every page fetches as the new user.
import Link from "next/link";
import { useEffect, useState } from "react";
import { errorMessage, signUp, useApi } from "@/lib/api";
import type { SignupOptions } from "@/lib/types";
import { Alert, Busy } from "@/components/ui";

export default function SignupPage() {
  const { data: options, error: optionsError } = useApi<SignupOptions>("/api/auth/signup-options");
  const [role, setRole] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>();
  const unitRole = !!options?.unit_roles.includes(role);
  const [search, setSearch] = useState(""); // keeps ?next= on the link; read after mount so server and browser render the same
  useEffect(() => setSearch(location.search), []);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const password = String(form.get("password") ?? "");
    if (password !== String(form.get("confirm") ?? "")) { setMessage("The two passwords do not match."); return; }
    setBusy(true); setMessage(undefined);
    try {
      await signUp({
        username: String(form.get("username") ?? "").trim(), name: String(form.get("name") ?? "").trim(), password, role,
        bu: unitRole ? String(form.get("bu") ?? "") : null,
      });
      const next = new URLSearchParams(location.search).get("next");
      location.assign(next?.startsWith("/") && !next.startsWith("//") ? next : "/");
    } catch (err) { setMessage(errorMessage(err)); setBusy(false); }
  }
  return (
    <div className="login">
      <form className="card form compact" onSubmit={submit} aria-busy={busy}>
        <h1><span className="brand-mark" aria-hidden>L0</span> Create your Layer 0 account</h1>
        <label>Username <input name="username" required minLength={3} maxLength={40} pattern="[A-Za-z0-9._\-]+" title="Letters, numbers, dot, underscore or hyphen" autoComplete="username" autoFocus disabled={busy} /></label>
        <label>Display name <input name="name" required minLength={2} maxLength={80} autoComplete="name" disabled={busy} />
          <span className="muted">Shown on everything you do.</span></label>
        <label>Password <input name="password" type="password" required minLength={10} autoComplete="new-password" disabled={busy} />
          <span className="muted">At least 10 characters.</span></label>
        <label>Confirm password <input name="confirm" type="password" required minLength={10} autoComplete="new-password" disabled={busy} /></label>
        <label>Role
          <select name="role" required value={role} onChange={(e) => setRole(e.target.value)} disabled={busy || !options}>
            <option value="">Select a role…</option>
            {Object.entries(options?.roles ?? {}).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
          </select></label>
        {unitRole && (
          <label>Unit
            <select name="bu" required defaultValue="" disabled={busy}>
              <option value="">Select a unit…</option>
              {Object.entries(options?.units ?? {}).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
            </select></label>
        )}
        <button disabled={busy || !options}>Create account</button>
        {busy && <Busy label="Creating your account…" />}
        <Alert kind="error">{message ?? (optionsError ? `Could not load the sign-up options: ${optionsError}` : undefined)}</Alert>
        <p className="muted">Choose the role you work in. Your role decides what you can do; a pilot will assign roles centrally.</p>
        <p className="muted">Already have an account? <Link href={`/login${search}`}>Sign in</Link></p>
      </form>
    </div>
  );
}
