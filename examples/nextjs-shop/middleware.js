import { NextResponse } from "next/server";

const PUBLIC = ["/login", "/api/login", "/logo.svg", "/favicon.svg"];

// DEMO ONLY: any "shop_session" cookie counts as signed in (see lib/auth.js). Fine for a local example app
// with fake data; a real app must verify the session.
export function middleware(req) {
  const { pathname } = req.nextUrl;
  if (PUBLIC.some((p) => pathname.startsWith(p)) || pathname.startsWith("/_next")) return NextResponse.next();
  if (!req.cookies.get("shop_session")) {
    if (pathname.startsWith("/api/")) return NextResponse.json({ error: "Please sign in" }, { status: 401 });
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = { matcher: ["/((?!_next/static|_next/image).*)"] };
