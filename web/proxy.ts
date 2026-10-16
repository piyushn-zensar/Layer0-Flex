// Page guard (P-31, C-26): a visitor without the sign-in cookie goes to /login and comes back to the page asked for.
// The API stays the control (every /api route answers 401 without a valid token); this only avoids empty screens.
// Next 16 names this file proxy.ts (the plan's web/middleware.ts: that file name is deprecated in Next 16).  Owner: Piyush.
import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  if (request.cookies.has("layer0_token")) return NextResponse.next();
  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = `?next=${encodeURIComponent(request.nextUrl.pathname + request.nextUrl.search)}`;
  return NextResponse.redirect(url);
}

// Everything except the API (proxied to FastAPI), Next's own files, the sign-in and sign-up pages and static files.
export const config = { matcher: ["/((?!api|_next|login|signup|favicon\\.ico|.*\\..*).*)"] };
