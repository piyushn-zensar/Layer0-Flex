"use client";
// PoC user picker: bid manager, or a unit's product manager / design engineer.  Owner: Janvia.
// Changing it sets the "actor" cookie (sent as X-Actor) and reloads, so every page re-fetches as that person.
import { useEffect, useState } from "react";
import { currentActor, setActor, useApi } from "@/lib/api";

export default function ActorPicker() {
  const { data: people } = useApi<{ name: string; bu: string | null }[]>("/api/people");
  const [actor, setLocal] = useState("Bid Manager");
  useEffect(() => setLocal(currentActor()), []);
  return (
    <div className="actor" data-tour="shell-actor">
      <label htmlFor="actor-select">Acting as</label>
      <select id="actor-select" value={actor} title="Switch the person acting in this PoC"
        onChange={(e) => { setActor(e.target.value); location.reload(); }}>
        {(people ?? [{ name: actor, bu: null }]).map((p) => <option key={p.name}>{p.name}</option>)}
      </select>
    </div>
  );
}
