// Root layout: the page chrome is components/shell/Shell (top bar, signed-in user, toasts, walkthrough; none of it in a detached pane window).  Owner: Janvia.
import type { Metadata } from "next";
import Shell from "@/components/shell/Shell";
import "./globals.css";
// One stylesheet per page group, after the foundation so page rules win on equal specificity.
import "./styles/overview.css";
import "./styles/requirements.css";
import "./styles/trace.css";
import "./styles/workspace.css"; // J-18: pane order, splitters, detached panes
import "./styles/consolidation.css";
import "./styles/tour.css";

export const metadata: Metadata = { title: "Layer 0", description: "Bid workflow PoC" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
