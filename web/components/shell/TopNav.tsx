"use client";
// Global navigation: three destinations, the current one highlighted.  Owner: Janvia.
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/portfolio", label: "Opportunities", match: ["/portfolio", "/opportunities/"] },
  { href: "/inbox", label: "My work", match: ["/inbox"] },
  { href: "/catalog", label: "Product catalog", match: ["/catalog"] },
];

export default function TopNav() {
  const path = usePathname();
  return (
    <nav className="topnav" aria-label="Main">
      {LINKS.map((l) => {
        const active = l.match.some((m) => path.startsWith(m)) && path !== "/opportunities/new";
        return <Link key={l.href} href={l.href} className={active ? "active" : ""} aria-current={active ? "page" : undefined}>{l.label}</Link>;
      })}
    </nav>
  );
}
