// Every opportunity page shows the step navigation.  Owner: Janvia.
import OppSteps from "@/components/shell/OppSteps";

export default function OpportunityLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <OppSteps />
      <div className="content">{children}</div>
    </>
  );
}
