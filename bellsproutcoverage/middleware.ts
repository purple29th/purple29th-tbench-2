import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(req: NextRequest) {
  // Allow public assets and auth routes
  const path = req.nextUrl.pathname;
  if (
    path.startsWith("/api/auth") ||
    path.startsWith("/_next") ||
    path.startsWith("/favicon") ||
    path === "/login"
  ) {
    return NextResponse.next();
  }

  // If NEXTAUTH_SECRET not set (local dev without env), allow all for testing
  // In production Vercel, set NEXTAUTH_SECRET + GITHUB_ID + GITHUB_SECRET
  if (!process.env.NEXTAUTH_SECRET) {
    return NextResponse.next();
  }

  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });

  if (!token) {
    // Not logged in → redirect to internal SSO login
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // token present → org check already done in signIn callback, allow
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico).*)"],
};
