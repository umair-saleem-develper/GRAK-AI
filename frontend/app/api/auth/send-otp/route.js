import { NextResponse } from "next/server";

const rawApiUrl =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.BACKEND_URL ||
  "http://localhost:8001";
const API_URL = rawApiUrl.replace(/\/+$/, "");

export async function POST(req) {
  try {
    const { email } = await req.json();

    if (!email) {
      return NextResponse.json(
        { message: "Email is required" },
        { status: 400 },
      );
    }

    // Call Python backend to handle generation, hashing, DB storage, and email delivery
    const response = await fetch(`${API_URL}/api/auth/send-otp`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: email, purpose: "login" }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { message: data.detail || "Failed to send OTP" },
        { status: response.status },
      );
    }

    return NextResponse.json(
      { message: "OTP sent successfully" },
      { status: 200 },
    );
  } catch (error) {
    console.error("Error in Next.js send-otp route:", error);
    return NextResponse.json(
      { message: "Failed to process OTP request" },
      { status: 500 },
    );
  }
}
