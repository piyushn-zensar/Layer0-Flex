// App shell: top bar and acting-user picker.  Owner: Janvia.
import type { Metadata } from "next";
import Link from "next/link";
import ActorPicker from "@/components/shell/ActorPicker";
import TopNav from "@/components/shell/TopNav";
import "./globals.css";

export const metadata: Metadata = { title: "Layer 0", description: "Opportunity workflow PoC" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <Link className="brand" href="/portfolio">Layer 0 <span>Opportunity workflow</span></Link>
          <TopNav />
          <div className="topbar-right">
            <Link className="button" href="/opportunities/new">New opportunity</Link>
            <ActorPicker />
          </div>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
