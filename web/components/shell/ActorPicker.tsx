"use client";
// Signed-in person (GET /api/auth/me) and a link to sign in as someone else.  Owner: Janvia.
// P-21 replaced the old picker; J-10 adds role, unit and Sign out.
import Link from "next/link";
import { useMe } from "@/lib/api";

export default function ActorPicker() {
  const me = useMe();
  return (
    <div className="actor" data-tour="shell-actor">
      <span>{me?.name ?? "…"}</span>
      <Link href="/login" title="Sign in as someone else">Switch</Link>
    </div>
  );
}
