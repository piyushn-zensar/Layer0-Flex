// Every opportunity page shows the step navigation; a pane opened in its own window (J-18) does not (components/shell/BidChrome).  Owner: Janvia.
import BidChrome from "@/components/shell/BidChrome";

export default function OpportunityLayout({ children }: { children: React.ReactNode }) {
  return <BidChrome>{children}</BidChrome>;
}
