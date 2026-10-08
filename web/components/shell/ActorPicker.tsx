"use client";
// PoC user picker: bid manager, or a unit's product manager / design engineer.  Owner: Janvia.
import { useEffect, useState } from "react";
import { currentActor, setActor, useApi } from "@/lib/api";

export default function ActorPicker() {
  const { data: people } = useApi<{ name: string; bu: string | null }[]>("/api/people");
  const [actor, setLocal] = useState("Bid Manager");
  useEffect(() => setLocal(currentActor()), []);
  return (
    <label className="actor">
      Acting as
      <select value={actor} onChange={(e) => { setActor(e.target.value); location.reload(); }}>
        {(people ?? [{ name: actor, bu: null }]).map((p) => <option key={p.name}>{p.name}</option>)}
      </select>
    </label>
  );
}
