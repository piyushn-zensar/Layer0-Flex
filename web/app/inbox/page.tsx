"use client";
// "My work": open the inbox of the acting user's business unit (bid manager -> bid desk).  Owner: Atharv.
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, currentActor, errorMessage } from "@/lib/api";
import { Alert, Busy } from "@/components/ui";

export default function MyInbox() {
  const router = useRouter();
  const [error, setError] = useState<string>();
  useEffect(() => {
    api<{ name: string; bu: string | null }[]>("/api/people").then((people) => {
      const me = people.find((p) => p.name === currentActor());
      router.replace(`/inbox/${me?.bu ?? "BID"}`);
    }, (e) => setError(errorMessage(e)));
  }, [router]);
  return (
    <div className="content">
      {error ? <Alert kind="error">Could not find your work package: {error}. Refresh to try again.</Alert>
        : <Busy label="Opening your work package…" />}
    </div>
  );
}
