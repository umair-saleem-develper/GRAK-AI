import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const rawApiUrl =
      process.env.NEXT_PUBLIC_API_URL ||
      process.env.BACKEND_URL ||
      "http://localhost:8001";
    const apiBase = rawApiUrl.replace(/\/+$/, "");

    // Check backend health silently
    const res = await fetch(`${apiBase}/health`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      // 3.5s timeout for cold-start checking
      signal: AbortSignal.timeout(3500),
    });

    if (res.ok) {
      return NextResponse.json({ status: "ok" }, { status: 200 });
    }

    // Return 200 even if backend returns 500, to suppress browser console red errors
    return NextResponse.json({ status: "offline" }, { status: 200 });
  } catch (err) {
    // Return 200 on connection refused, preventing browser fetch errors
    return NextResponse.json({ status: "offline" }, { status: 200 });
  }
}
