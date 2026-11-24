"use client";
import { useState, Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { auth } from "@/lib/firebase";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
} from "firebase/auth";
import { API_URL } from "@/lib/apiClient";

function EmailPasswordForm({ isModal }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();

  const [emailState, setEmailState] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resetSent, setResetSent] = useState(false);

  useEffect(() => {
    const e = searchParams.get("email");
    if (e) setEmailState(e);
  }, [searchParams]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      let userCredential;
      if (isSignUp) {
        userCredential = await createUserWithEmailAndPassword(
          auth,
          emailState,
          password,
        );
      } else {
        userCredential = await signInWithEmailAndPassword(
          auth,
          emailState,
          password,
        );
      }

      const idToken = await userCredential.user.getIdToken();

      const response = await fetch(`${API_URL}/api/auth/firebase`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: idToken }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Backend authentication failed");
      }

      await login(data.data.access_token);

      if (isModal) {
        router.back();
      } else {
        router.push("/");
      }
    } catch (err) {
      console.error("Login Error:", err.message);
      if (
        err.code === "auth/user-not-found" ||
        err.code === "auth/wrong-password" ||
        err.code === "auth/invalid-credential"
      ) {
        setError("Invalid email or password.");
      } else if (err.code === "auth/email-already-in-use") {
        setError("Email already in use. Please sign in instead.");
      } else {
        setError(err.message || "Authentication failed.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!emailState) return;
    try {
      await sendPasswordResetEmail(auth, emailState);
      setResetSent(true);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center min-h-screen w-full bg-[#0b0a0f] text-white z-[100] font-sans">
      {/* Premium background glow */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full pointer-events-none opacity-20 blur-[120px]"
        style={{
          background:
            "radial-gradient(circle, rgba(157,0,255,0.8) 0%, rgba(157,0,255,0) 70%)",
        }}
      ></div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-[420px] relative z-10 px-4 flex flex-col items-center"
      >
        <div className="bg-[#131217]/80 backdrop-blur-2xl rounded-[24px] p-8 shadow-2xl border border-white/5 flex flex-col items-center w-full">
          <button
            className="absolute top-5 right-5 text-gray-500 hover:text-white transition-colors"
            onClick={() => router.back()}
          >
            ✕
          </button>

          <h1 className="text-2xl font-medium tracking-tight mb-2 mt-4">
            {isSignUp ? "Create an account" : "Enter your password"}
          </h1>

          <p className="text-gray-400 mb-8 text-center text-[15px]">
            {emailState}
          </p>

          {error && (
            <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 px-4 py-3 rounded-xl mb-6 w-full text-center">
              {error}
            </div>
          )}
          {resetSent && (
            <div className="text-green-400 text-sm bg-green-500/10 border border-green-500/20 px-4 py-3 rounded-xl mb-6 w-full text-center">
              Password reset email sent!
            </div>
          )}

          <form onSubmit={handleLogin} className="w-full flex flex-col gap-3">
            <input
              type="password"
              placeholder="Password"
              className="w-full bg-[#1a1920] border border-white/10 text-white placeholder-gray-500 rounded-xl px-4 py-3 outline-none focus:border-purple-500/50 focus:bg-[#201f25] transition-all"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <button
              type="submit"
              className="w-full bg-white text-black font-semibold py-3 rounded-full hover:bg-gray-200 transition-colors mt-2"
              disabled={loading}
            >
              {loading ? (
                <div className="flex justify-center items-center">
                  <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
                </div>
              ) : (
                "Continue"
              )}
            </button>
          </form>

          <div className="flex flex-col items-center mt-6 gap-3">
            {!isSignUp && (
              <p className="text-[13px] text-gray-400">
                Don't have an account?{" "}
                <button
                  onClick={() => setIsSignUp(true)}
                  className="text-purple-400 hover:underline hover:text-purple-300 transition-colors"
                >
                  Sign up
                </button>
              </p>
            )}
            {isSignUp && (
              <p className="text-[13px] text-gray-400">
                Already have an account?{" "}
                <button
                  onClick={() => setIsSignUp(false)}
                  className="text-purple-400 hover:underline hover:text-purple-300 transition-colors"
                >
                  Log in
                </button>
              </p>
            )}

            {!isSignUp && (
              <button
                onClick={handleResetPassword}
                className="text-[13px] text-purple-400 hover:underline hover:text-purple-300 transition-colors"
              >
                Forgot password?
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export default function EmailPassword({ isModal }) {
  return (
    <Suspense
      fallback={
        <div className="fixed inset-0 flex items-center justify-center bg-[#0b0a0f] z-[100]">
          <div className="w-8 h-8 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"></div>
        </div>
      }
    >
      <EmailPasswordForm isModal={isModal} />
    </Suspense>
  );
}
