import { NextResponse } from "next/server";

const rawApiUrl =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.BACKEND_URL ||
  "http://localhost:8001";
const API_URL = rawApiUrl.replace(/\/+$/, "");

export async function POST(req) {
  try {
    const { email, code } = await req.json();

    if (!email || !code) {
      return NextResponse.json(
        { message: "Email and code are required" },
        { status: 400 },
      );
    }

    // Call Python backend to validate OTP and issue session tokens
    const verifyResponse = await fetch(`${API_URL}/api/auth/verify-otp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email.trim(),
        code: code.trim(),
        purpose: "login",
      }),
    });

    const verifyData = await verifyResponse.json();

    if (!verifyResponse.ok) {
      return NextResponse.json(
        { message: verifyData.detail || "Failed to verify OTP" },
        { status: verifyResponse.status },
      );
    }

    const response = NextResponse.json(
      {
        message: "Verified successfully",
        data: {
          access_token: verifyData.data.access_token,
        },
      },
      { status: 200 },
    );

    const setCookieHeader = verifyResponse.headers.get("set-cookie");
    if (setCookieHeader) {
      response.headers.set("Set-Cookie", setCookieHeader);
    }

    return response;
  } catch (error) {
    console.error("Error verifying OTP in Next.js:", error);
    return NextResponse.json(
      { message: "Failed to verify OTP" },
      { status: 500 },
    );
  }
}
