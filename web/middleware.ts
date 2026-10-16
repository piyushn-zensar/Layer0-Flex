// Sign-in guard (P-31): a page request without the sign-in cookie goes to /login?next=<where it was going>.
// Only checks the cookie is present; the API verifies it (an expired token still gets lib/api's 401 redirect).
import { NextResponse, type NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  if (req.cookies.has("layer0_token")) return NextResponse.next();
  const url = req.nextUrl.clone();
  url.pathname = "/login";
  url.search = `?next=${encodeURIComponent(req.nextUrl.pathname + req.nextUrl.search)}`;
  return NextResponse.redirect(url);
}

// Pages only: not /api, /_next, /login, /signup, the favicon, or any path with a dot (favicon, static files).
export const config = { matcher: ["/((?!api|_next|login|signup|.*[.].*).*)"] };
