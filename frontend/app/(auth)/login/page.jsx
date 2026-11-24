"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { auth, GoogleAuthProvider } from "@/lib/firebase";
import {
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
} from "firebase/auth";
import { useAuth } from "@/context/AuthContext";
import { API_URL } from "@/lib/apiClient";
import Image from "next/image";

export default function Login({ isModal }) {
  const router = useRouter();
  const { session, login } = useAuth();
  const [email, setEmail] = useState("");
  const [step, setStep] = useState("email");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const timeoutRef = useRef(null);
  const emailInputRef = useRef(null);

  useEffect(() => {
    const handleHighlight = () => {
      if (emailInputRef.current) {
        emailInputRef.current.focus();

        // Force instant OFF state
        emailInputRef.current.style.transition = "none";
        emailInputRef.current.classList.remove(
          "ring-4",
          "ring-purple-500/20",
          "dark:ring-purple-400/30",
          "border-purple-500/80",
          "dark:border-purple-400/80",
          "shadow-[0_0_15px_rgba(168,85,247,0.3)]",
          "scale-[1.02]",
        );
        emailInputRef.current.classList.add(
          "border-[#E5E5E5]",
          "dark:border-white/20",
        );

        // Force browser reflow so it registers the OFF state
        void emailInputRef.current.offsetWidth;

        // Force instant ON state
        emailInputRef.current.classList.remove(
          "border-[#E5E5E5]",
          "dark:border-white/20",
        );
        emailInputRef.current.classList.add(
          "ring-4",
          "ring-purple-500/20",
          "dark:ring-purple-400/30",
          "border-purple-500/80",
          "dark:border-purple-400/80",
          "shadow-[0_0_15px_rgba(168,85,247,0.3)]",
          "scale-[1.02]",
        );

        if (timeoutRef.current) clearTimeout(timeoutRef.current);

        // Smooth fade out after a short delay
        timeoutRef.current = setTimeout(() => {
          if (emailInputRef.current) {
            emailInputRef.current.style.transition = "all 0.3s ease-out";
            emailInputRef.current.classList.remove(
              "ring-4",
              "ring-purple-500/20",
              "dark:ring-purple-400/30",
              "border-purple-500/80",
              "dark:border-purple-400/80",
              "shadow-[0_0_15px_rgba(168,85,247,0.3)]",
              "scale-[1.02]",
            );
            emailInputRef.current.classList.add(
              "border-[#E5E5E5]",
              "dark:border-white/20",
            );
          }
        }, 150);
      }
    };
    window.addEventListener("highlightAuth", handleHighlight);
    return () => {
      window.removeEventListener("highlightAuth", handleHighlight);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  // AuthGuard now handles all routing protection and redirects centrally.

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/auth/send-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to send code");
      setStep("otp");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    if (!otp) return;
    setLoading(true);
    setError("");

    // As requested: Add a console.log right before the API call
    console.log("Sending OTP Verification:", { email, code: otp });

    try {
      const res = await fetch("/api/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code: otp }), // Sending correct JSON format
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || "Failed to verify code");
      }

      // Successfully logged in via custom Next.js backend!
      await login(data.data.access_token);

      if (isModal) {
        router.back();
      } else {
        router.push("/");
      }
    } catch (err) {
      console.error("OTP Submit Error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/auth/send-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to send code");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = (e) => {
    e?.preventDefault();
    if (loading) return;

    const provider = new GoogleAuthProvider();
    provider.setCustomParameters({ prompt: "select_account" });

    // Start the popup COMPLETELY synchronously (no async/await before it).
    // This prevents Babel/Turbopack from turning this into a microtask which breaks the "trusted event" chain.
    const popupPromise = signInWithPopup(auth, provider);

    // Now update React state to show the loading spinner immediately
    setLoading(true);
    setError("");

    popupPromise
      .then((result) => {
        return result.user.getIdToken();
      })
      .then((idToken) => {
        return fetch("/api/auth/firebase", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${idToken}`,
          },
          credentials: "include",
        });
      })
      .then((response) => {
        return response.json().then((data) => {
          if (!response.ok) {
            throw new Error(data.detail || "Backend authentication failed");
          }
          return data.data.access_token;
        });
      })
      .then((access_token) => {
        return login(access_token);
      })
      .then(() => {
        if (isModal) {
          router.back();
        } else {
          router.push("/");
        }
      })
      .catch((err) => {
        if (
          err.code === "auth/popup-closed-by-user" ||
          err.code === "auth/cancelled-popup-request"
        ) {
          // Silently ignore user cancellations to prevent Next.js dev overlay
          setLoading(false);
          return;
        }
        if (err.code === "auth/popup-blocked") {
          // Do not use console.error here either, so dev overlay doesn't pop up for browser settings
          console.warn("Popup blocked by browser.");
          setError(
            "Popup was blocked by your browser. Please allow popups for this site and try again.",
          );
          setLoading(false);
          return;
        }
        console.error("Google Login Error:", err);
        setError(
          "Google Login Failed: " + (err.message || "Please try again."),
        );
        setLoading(false);
      });
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="w-full relative z-10"
    >
      <div className="bg-white dark:bg-[#131217]/80 backdrop-blur-2xl rounded-[24px] p-8 shadow-[0_8px_30px_rgb(0,0,0,0.06)] dark:shadow-2xl border border-[#E5E5E5] dark:border-white/5 flex flex-col items-center w-full">
        {/* Removed back button since this is now a main landing view */}
        <h2 className="text-xl font-medium tracking-tight mb-6 w-full text-center">
          Log in or sign up
        </h2>

        {error && (
          <div className="text-red-500 dark:text-red-400 text-sm bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 px-4 py-3 rounded-xl mb-6 w-full text-center">
            {error}
          </div>
        )}

        <button
          type="button"
          className="w-full flex items-center justify-center gap-3 bg-white dark:bg-white/5 border border-[#E5E5E5] dark:border-white/10 text-gray-900 dark:text-white font-medium py-3 px-4 rounded-xl mb-4 hover:bg-gray-50 dark:hover:bg-white/10 transition-colors shadow-sm dark:shadow-none disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={loginWithGoogle}
          disabled={loading}
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-gray-400 border-t-gray-800 dark:border-white/30 dark:border-t-white rounded-full animate-spin"></div>
              <span>Loading...</span>
            </>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Continue with Google
            </>
          )}
        </button>

        <div className="flex items-center w-full my-4">
          <div className="flex-grow h-px bg-[#E5E5E5] dark:bg-white/10"></div>
          <span className="px-3 text-xs text-gray-500 uppercase">Or</span>
          <div className="flex-grow h-px bg-[#E5E5E5] dark:bg-white/10"></div>
        </div>

        {step === "email" ? (
          <>
            <form
              onSubmit={handleEmailSubmit}
              className="w-full flex flex-col gap-3"
            >
              <input
                ref={emailInputRef}
                type="email"
                placeholder="Enter your email"
                className="w-full bg-white dark:bg-transparent border border-[#E5E5E5] dark:border-white/20 text-gray-900 dark:text-white placeholder-gray-500 rounded-xl px-4 py-3 outline-none focus:border-primary focus:ring-1 focus:ring-primary focus:bg-white dark:focus:bg-white/5 transition-all shadow-sm dark:shadow-none"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <button
                type="submit"
                className="w-full bg-[#191919] dark:bg-white text-white dark:text-black font-semibold py-3 rounded-xl hover:bg-black dark:hover:bg-gray-200 transition-colors mt-2 disabled:opacity-50"
                disabled={loading}
              >
                {loading ? "Sending..." : "Continue with email"}
              </button>
            </form>

            <p className="text-center text-[13px] text-gray-500 dark:text-gray-400 mt-6 w-full">
              By continuing, you acknowledge Grak AI's{" "}
              <a
                href="#"
                className="underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Privacy Policy
              </a>
              .
            </p>
          </>
        ) : (
          <div className="w-full flex flex-col items-center">
            <p className="text-gray-500 dark:text-gray-400 mb-6 text-center text-sm">
              Enter the verification code sent to
              <br />
              <strong className="text-gray-900 dark:text-white">{email}</strong>
            </p>
            <form
              onSubmit={handleOtpSubmit}
              className="w-full flex flex-col gap-3"
            >
              <input
                type="text"
                placeholder="Enter verification code"
                className="w-full bg-white dark:bg-transparent border border-[#E5E5E5] dark:border-white/20 text-gray-900 dark:text-white placeholder-gray-500 rounded-xl px-4 py-3 outline-none focus:border-primary focus:ring-1 focus:ring-primary focus:bg-white dark:focus:bg-white/5 transition-all text-center tracking-widest text-lg shadow-sm dark:shadow-none"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
                autoFocus
              />
              <button
                type="submit"
                className="w-full bg-[#191919] dark:bg-white text-white dark:text-black font-semibold py-3 rounded-xl hover:bg-black dark:hover:bg-gray-200 transition-colors mt-2 disabled:opacity-50"
                disabled={loading}
              >
                {loading ? "Verifying..." : "Verify Email Address"}
              </button>
            </form>

            <div className="text-center text-[13px] text-gray-500 dark:text-gray-400 mt-6 flex flex-col gap-1">
              <p>
                Not seeing the email in your inbox?{" "}
                <button
                  type="button"
                  onClick={handleResend}
                  className="underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition-colors"
                  disabled={loading}
                >
                  Try sending again.
                </button>
              </p>
              <p>
                Wrong email?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setStep("email");
                    setOtp("");
                  }}
                  className="underline underline-offset-2 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  Change email address
                </button>
              </p>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
