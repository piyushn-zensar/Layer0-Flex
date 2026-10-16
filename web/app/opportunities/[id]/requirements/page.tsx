// The Requirements page moved into pane 2 of Requirement Traceability (A-26, C-30): old links and bookmarks land there.
// Owner: Atharv (iteration 3).
import { redirect } from "next/navigation";

export default async function RequirementsRedirect({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  redirect(`/opportunities/${id}/trace`);
}
