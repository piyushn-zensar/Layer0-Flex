"use client";
// "My work": open the inbox of the acting user's business unit (bid manager -> bid desk).  Owner: Atharv.
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, currentActor } from "@/lib/api";

export default function MyInbox() {
  const router = useRouter();
  const [error, setError] = useState<string>();
  useEffect(() => {
    api<{ name: string; bu: string | null }[]>("/api/people").then((people) => {
      const me = people.find((p) => p.name === currentActor());
      router.replace(`/inbox/${me?.bu ?? "BID"}`);
    }, (e) => setError(String(e)));
  }, [router]);
  return error ? <p className="content warn">Could not find your work package: {error}. Refresh to try again.</p>
    : <p className="content">Opening your work package…</p>;
}
