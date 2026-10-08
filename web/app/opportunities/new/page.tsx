"use client";
// New opportunity.  Owner: Piyush.
import { useRouter } from "next/navigation";
import { post } from "@/lib/api";
import type { Opportunity } from "@/lib/types";

const CUSTOMER_TYPES = ["utility", "hyperscaler", "neocloud", "colocation", "silicon provider", "public sector"];

export default function NewOpportunityPage() {
  const router = useRouter();
  async function create(form: FormData) {
    const opp = await post<Opportunity>("/api/opportunities", Object.fromEntries(form));
    router.push(`/opportunities/${opp.id}`);
  }
  return (
    <div className="content">
      <h1>New opportunity</h1>
      <form className="card form" action={create}>
        <label>Title <input name="title" required placeholder="e.g. Syracuse switchgear procurement" /></label>
        <label>Customer <input name="customer" /></label>
        <label>Customer type
          <select name="customer_type"><option value="">—</option>{CUSTOMER_TYPES.map((t) => <option key={t}>{t}</option>)}</select>
        </label>
        <button>Create</button>
      </form>
    </div>
  );
}
