"use client";
// The signed-in person in the top bar: name, role and unit from GET /api/auth/me, and Sign out.  Owner: Janvia.
// Every page inherits it from app/layout.tsx. Signing in as someone else is the sign-in page (Sign out goes there).
import { signOut, useMe } from "@/lib/api";

export default function UserMenu() {
  const me = useMe();
  return (
    <div className="actor" data-tour="shell-actor">
      <div className="actor-id" aria-live="polite">
        <strong>{me?.name ?? "…"}</strong>
        {me && <span>{me.role_label} · {me.bu ?? "No unit"}</span>}
      </div>
      <button type="button" className="secondary sm" onClick={() => signOut()}>Sign out</button>
    </div>
  );
}
