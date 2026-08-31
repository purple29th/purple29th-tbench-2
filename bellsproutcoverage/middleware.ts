import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname;
  // Allow login, api, static, public files
  if (
    path.startsWith("/api") ||
    path.startsWith("/_next") ||
    path === "/login" ||
    path.startsWith("/favicon") ||
    path === "/robots.txt" ||
    path === "/security.txt" ||
    path === "/team_coverage.json"
  ) {
    return NextResponse.next();
  }

  // Strict SSO before page lands — check for internal SSO cookie
  // This simulates Meta internal device SSO: on phone without login, you get blocked at login page
  // Real Meta SSO would check X-Meta-Device-Cert, but we simulate with cookie set after SSO button
  const ssoCookie = req.cookies.get("bellsprout_internal_sso")?.value;

  if (!ssoCookie || ssoCookie !== "meta_passed") {
    // Not logged in via internal SSO → redirect to login (strictly before page)
    return NextResponse.redirect(new URL("/login", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
