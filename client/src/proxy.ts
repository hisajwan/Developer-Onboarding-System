import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { SESSION_COOKIE } from "@/config/session";

// Optimistic check only: no cookie means no session, so go to /login. Whether the cookie is
// actually valid is decided by the backend (see getSession in lib/api/session.ts).
export function proxy(request: NextRequest) {
  if (!request.cookies.has(SESSION_COOKIE)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

// Everything except the API proxy, the login/signup pages and static assets.
export const config = {
  matcher: ["/((?!api|login|signup|_next/static|_next/image|favicon.ico).*)"],
};
