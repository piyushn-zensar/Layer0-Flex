"use client";
// The app shell: top bar, signed-in user, toasts and the guided walkthrough. A pane opened in its own window (J-18, /trace/pane/{n}) gets none
// of it, only the toasts: no navigation chrome, and no walkthrough, which runs in the main window only.  Owner: Janvia.
import Link from "next/link";
import { usePathname } from "next/navigation";
import TopNav from "@/components/shell/TopNav";
import UserMenu from "@/components/shell/UserMenu";
import { ToastProvider } from "@/components/ui/Toast";
import { TourLauncher, TourOverlay, TourProvider, WalkthroughButton } from "@/components/tour";
import { isPaneWindowPath } from "@/components/workspace/types";
import { useMe } from "@/lib/api";

// Only the bid manager (and the administrator, who reads) starts a bid: the unit roles do not see New bid.
function NewBid() {
  const me = useMe();
  if (me?.role !== "bid_manager" && me?.role !== "admin") return null;
  return <Link className="button" href="/opportunities/new" data-tour="shell-new-opportunity">New bid</Link>;
}

export default function Shell({ children }: { children: React.ReactNode }) {
  if (isPaneWindowPath(usePathname())) return <ToastProvider><div className="pane-window">{children}</div></ToastProvider>;
  return (
    <ToastProvider>
      {/* The guided walkthrough (components/tour) wraps the shell so its button, overlay and dialog share one state. */}
      <TourProvider>
        <header className="topbar">
          <Link className="brand" href="/portfolio" data-tour="shell-brand"><span className="brand-mark" aria-hidden>L0</span>Layer 0 <span className="brand-sub">Bid workflow</span></Link>
          <TopNav />
          <div className="topbar-right">
            <NewBid />
            <UserMenu />
            <WalkthroughButton />
          </div>
        </header>
        <main>{children}</main>
        <TourOverlay />
        <TourLauncher />
      </TourProvider>
    </ToastProvider>
  );
}
