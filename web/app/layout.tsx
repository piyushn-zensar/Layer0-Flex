// App shell: top bar and acting-user picker.  Owner: Janvia.
import type { Metadata } from "next";
import Link from "next/link";
import ActorPicker from "@/components/shell/ActorPicker";
import "./globals.css";

export const metadata: Metadata = { title: "Layer 0", description: "Opportunity workflow PoC" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <Link className="brand" href="/portfolio">Layer 0 <span>opportunity workflow · PoC</span></Link>
          <nav>
            <Link href="/portfolio">Portfolio</Link>
            <Link href="/opportunities/new">New opportunity</Link>
            <Link href="/inbox">My work</Link>
            <Link href="/catalog">Catalog</Link>
          </nav>
          <ActorPicker />
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
