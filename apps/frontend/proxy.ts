import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const backendUrl = process.env.API_URL ?? "http://localhost:8000";
  // Use request.url (not nextUrl.pathname) to preserve trailing slashes
  // which Next.js strips from nextUrl before proxy runs
  const suffix = request.url.replace(/^https?:\/\/[^/]+\/backend/, "");
  const target = new URL(suffix || "/", backendUrl);
  return NextResponse.rewrite(target);
}

export const config = {
  matcher: "/backend/:path*",
};
