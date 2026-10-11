// App shell: top bar, acting-user picker and the toast region.  Owner: Janvia.
import type { Metadata } from "next";
import Link from "next/link";
import ActorPicker from "@/components/shell/ActorPicker";
import TopNav from "@/components/shell/TopNav";
import { ToastProvider } from "@/components/ui/Toast";
import "./globals.css";
// One stylesheet per page group, after the foundation so page rules win on equal specificity.
import "./styles/overview.css";
import "./styles/requirements.css";
import "./styles/trace.css";
import "./styles/consolidation.css";

export const metadata: Metadata = { title: "Layer 0", description: "Opportunity workflow PoC" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ToastProvider>
          <header className="topbar">
            <Link className="brand" href="/portfolio"><span className="brand-mark" aria-hidden>L0</span>Layer 0 <span className="brand-sub">Opportunity workflow</span></Link>
            <TopNav />
            <div className="topbar-right">
              <Link className="button" href="/opportunities/new">New opportunity</Link>
              <ActorPicker />
            </div>
          </header>
          <main>{children}</main>
        </ToastProvider>
      </body>
    </html>
  );
}
