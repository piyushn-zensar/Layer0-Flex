"use client";
// Step navigation for one opportunity.  Owner: Janvia.
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useApi } from "@/lib/api";
import type { Opportunity } from "@/lib/types";

const STEPS = [["", "1 Documents"], ["/requirements", "2 Requirements"], ["/trace", "3 Three screens"],
  ["/decisions", "4 Decisions"], ["/consolidation", "5 Consolidation"], ["/changes", "6 Changes"]];

export default function OppSteps() {
  const { id } = useParams<{ id: string }>();
  const path = usePathname();
  const { data } = useApi<{ opportunity: Opportunity }>(`/api/opportunities/${id}`);
  const base = `/opportunities/${id}`;
  return (
    <nav className="steps">
      <strong>{id}</strong> {data?.opportunity.title} {data && <span className="badge">{data.opportunity.status}</span>}
      {STEPS.map(([suffix, label]) => (
        <Link key={label} href={base + suffix} className={path === base + suffix ? "active" : ""}>{label}</Link>
      ))}
    </nav>
  );
}
