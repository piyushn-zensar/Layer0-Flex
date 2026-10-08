"use client";
// "My work": open the inbox of the acting user's business unit (bid manager -> bid desk).  Owner: Atharv.
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { api, currentActor } from "@/lib/api";

export default function MyInbox() {
  const router = useRouter();
  useEffect(() => {
    api<{ name: string; bu: string | null }[]>("/api/people").then((people) => {
      const me = people.find((p) => p.name === currentActor());
      router.replace(`/inbox/${me?.bu ?? "BID"}`);
    });
  }, [router]);
  return <p className="content">Opening your work package…</p>;
}
