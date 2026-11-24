"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/apiClient";
import { auth } from "@/lib/firebase";
import { RecaptchaVerifier, signInWithPhoneNumber } from "firebase/auth";
import { motion } from "framer-motion";

export default function PhoneLogin() {
  const router = useRouter();
  const [countryCode, setCountryCode] = useState("92");
  const [localPhoneNumber, setLocalPhoneNumber] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(1); // 1 = Phone, 2 = OTP
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // Clear any existing verifier instance from previous renders (Strict Mode fix)
    if (window.recaptchaVerifier) {
      try {
        window.recaptchaVerifier.clear();
      } catch (e) {
        console.warn("Could not clear recaptcha", e);
      }
      window.recaptchaVerifier = null;
    }

    // Delay initialization slightly to ensure DOM is ready
    setTimeout(() => {
      const container = document.getElementById("recaptcha-container");
      if (container) {
        window.recaptchaVerifier = new RecaptchaVerifier(
          auth,
          "recaptcha-container",
          {
            size: "invisible",
          },
        );
      }
    }, 100);

    return () => {
      if (window.recaptchaVerifier) {
        try {
          window.recaptchaVerifier.clear();
        } catch (e) {}
        window.recaptchaVerifier = null;
      }
    };
  }, []);

  const handleSendCode = async (e) => {
    e.preventDefault();
    if (!localPhoneNumber) return;
    setLoading(true);
    setError("");

    try {
      const appVerifier = window.recaptchaVerifier;
      const fullNumber = `+${countryCode}${localPhoneNumber.replace(/^0+/, "")}`; // Ensure no leading zero
      const confirmationResult = await signInWithPhoneNumber(
        auth,
        fullNumber,
        appVerifier,
      );
      window.confirmationResult = confirmationResult;
      setStep(2);
    } catch (err) {
      console.error(err);
      setError("Failed to send verification code: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const result = await window.confirmationResult.confirm(otp);
      const firebaseToken = await result.user.getIdToken();

      const response = await fetch(`${API_URL}/auth/phone`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: firebaseToken }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Phone login failed");
      }

      if (data.data?.access_token) {
        localStorage.setItem("access_token", data.data.access_token);
        localStorage.setItem("refresh_token", data.data.refresh_token);
        router.push("/");
      } else {
        throw new Error("Invalid response from server");
      }
    } catch (err) {
      console.error("Phone Auth Error:", err.message);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center min-h-screen w-full bg-black/60 backdrop-blur-sm text-white z-[100] font-sans">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="w-full max-w-[420px] relative z-10 flex flex-col items-center"
      >
        <button
          className="absolute top-0 right-0 text-gray-400 hover:text-white"
          onClick={() => router.back()}
        >
          ✕
        </button>

        <h1 className="text-[32px] font-bold mb-3 mt-4 text-center">
          {step === 1 ? "Verify your phone number" : "Check your phone"}
        </h1>
        <p className="text-gray-300 mb-8 text-center text-[16px]">
          {step === 1
            ? "We'll send you a 6-digit verification code."
            : "Enter the verification code we just sent."}
        </p>

        {error && (
          <div className="text-red-500 mb-4 text-center text-sm">{error}</div>
        )}

        <div id="recaptcha-container"></div>

        {step === 1 ? (
          <form
            onSubmit={handleSendCode}
            className="w-full flex flex-col gap-5"
          >
            <div className="relative w-full">
              <select
                className="w-full bg-transparent border border-gray-600 rounded-full px-5 py-4 text-white appearance-none focus:outline-none focus:border-white transition cursor-pointer text-[16px]"
                value={countryCode}
                onChange={(e) => setCountryCode(e.target.value)}
              >
                <option value="92" className="bg-[#202123]">
                  Pakistan +(92)
                </option>
                <option value="1" className="bg-[#202123]">
                  United States +(1)
                </option>
                <option value="44" className="bg-[#202123]">
                  United Kingdom +(44)
                </option>
                <option value="91" className="bg-[#202123]">
                  India +(91)
                </option>
                <option value="971" className="bg-[#202123]">
                  UAE +(971)
                </option>
              </select>
              <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-white">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
              </div>
            </div>

            <div className="relative w-full">
              <span className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-300 text-[16px]">
                +{countryCode}
              </span>
              <input
                type="tel"
                placeholder="Phone number"
                value={localPhoneNumber}
                onChange={(e) =>
                  setLocalPhoneNumber(e.target.value.replace(/[^0-9]/g, ""))
                }
                className="w-full bg-transparent border border-gray-600 rounded-full pl-16 pr-5 py-4 text-white focus:outline-none focus:border-white transition text-[16px] placeholder-gray-500"
                required
                autoFocus
              />
            </div>

            <button
              type="submit"
              className="w-full bg-white text-black font-semibold py-4 px-4 rounded-full hover:bg-gray-200 transition text-[16px] mt-2"
              disabled={loading}
            >
              {loading ? "Sending..." : "Continue"}
            </button>
          </form>
        ) : (
          <form
            onSubmit={handleVerifyOTP}
            className="w-full flex flex-col gap-6"
          >
            <div className="relative w-full">
              <input
                type="text"
                id="otpInput"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, ""))}
                className="w-full bg-transparent border border-[#7a82da] rounded-full px-5 py-4 text-white focus:outline-none transition peer placeholder-transparent"
                placeholder="Code"
                required
                maxLength={6}
                autoFocus
              />
              <label
                htmlFor="otpInput"
                className="absolute left-4 -top-3 bg-[#202123] px-1 text-[13px] text-[#7a82da] peer-placeholder-shown:text-gray-400 peer-placeholder-shown:top-4 peer-focus:-top-3 peer-focus:text-[#7a82da] transition-all cursor-text"
              >
                Code
              </label>
            </div>

            <button
              type="submit"
              className="w-full bg-white text-black font-semibold py-4 px-4 rounded-full hover:bg-gray-200 transition text-[16px]"
              disabled={loading}
            >
              {loading ? "Verifying..." : "Continue"}
            </button>
            <div className="text-center mt-4">
              <button
                type="button"
                className="text-white hover:underline font-medium"
                onClick={() => setStep(1)}
              >
                Change Phone Number
              </button>
            </div>
          </form>
        )}
      </motion.div>
    </div>
  );
}
