"use client";
// Global navigation: four destinations, the current one highlighted.  Owner: Janvia.
import Link from "next/link";
import { usePathname } from "next/navigation";

// `tour` is the data-tour id the guided walkthrough spotlights (web/tour/chapters/navigation.ts).
const LINKS = [
  { href: "/portfolio", label: "Opportunities", match: ["/portfolio", "/opportunities/"], tour: "shell-nav-opportunities" },
  { href: "/inbox", label: "My work", match: ["/inbox"], tour: "shell-nav-mywork" },
  { href: "/catalog", label: "Product catalog", match: ["/catalog"], tour: "shell-nav-catalog" },
  { href: "/knowledge", label: "Knowledge base", match: ["/knowledge"], tour: "shell-nav-knowledge" }, // A-11 curator queue
];

export default function TopNav() {
  const path = usePathname();
  return (
    <nav className="topnav" aria-label="Main" data-tour="shell-nav">
      {LINKS.map((l) => {
        const active = l.match.some((m) => path.startsWith(m)) && path !== "/opportunities/new";
        return <Link key={l.href} href={l.href} className={active ? "active" : ""} aria-current={active ? "page" : undefined} data-tour={l.tour}>{l.label}</Link>;
      })}
    </nav>
  );
}
