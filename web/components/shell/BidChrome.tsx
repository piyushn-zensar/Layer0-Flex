"use client";
// The bid header (step bar) and the page frame around every opportunity page; a detached pane window (J-18) has neither.  Owner: Janvia.
import { usePathname } from "next/navigation";
import OppSteps from "@/components/shell/OppSteps";
import { isPaneWindowPath } from "@/components/workspace/types";

export default function BidChrome({ children }: { children: React.ReactNode }) {
  if (isPaneWindowPath(usePathname())) return <>{children}</>;
  return (
    <>
      <OppSteps />
      <div className="content">{children}</div>
    </>
  );
}
