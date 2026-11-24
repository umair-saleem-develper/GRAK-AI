"use client";
import { useState, useEffect, Suspense } from "react";
import styles from "../../auth.module.css";
import { useRouter, useSearchParams } from "next/navigation";
import { API_URL } from "@/lib/apiClient";

function VerifyEmailForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailParam = searchParams.get("email") || "";

  const [email, setEmail] = useState(emailParam);
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(`${API_URL}/auth/verify-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Verification failed");
      }

      setSuccess("Email verified successfully! Redirecting...");
      setTimeout(() => {
        router.push("/");
      }, 1500);
    } catch (err) {
      console.error("Error verifying:", err.message);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    try {
      await fetch(`${API_URL}/auth/resend-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setSuccess("Verification code resent if email is registered.");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError("Failed to resend code");
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.authModal}>
        <h1 className={styles.title}>Verify Email</h1>
        <p className={styles.subtitle}>
          Enter the 6-digit code sent to your email.
        </p>

        {error && <div className={styles.errorMsg}>{error}</div>}
        {success && <div className={styles.successMsg}>{success}</div>}

        <form onSubmit={handleVerify}>
          <input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={styles.inputField}
            required
            readOnly={!!emailParam}
          />
          <input
            type="text"
            placeholder="Enter 6-digit OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            className={styles.otpInput}
            required
            maxLength={6}
            autoFocus
          />
          <button
            type="submit"
            className={styles.primaryButton}
            disabled={loading}
          >
            {loading ? "Verifying..." : "Verify Email"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "20px" }}>
          <button className={styles.link} onClick={handleResend}>
            Didn't receive a code? Resend
          </button>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmail() {
  return (
    <Suspense fallback={<div className={styles.authContainer}>Loading...</div>}>
      <VerifyEmailForm />
    </Suspense>
  );
}
