"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function requestOtp(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await auth.requestOtp(phone);
      setStep("otp");
    } catch (err: unknown) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  }

  async function verifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokens = await auth.verifyOtp(phone, otp);
      login(phone, tokens.access_token, tokens.refresh_token);
      router.push("/");
    } catch (err: unknown) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? "Invalid OTP");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center mx-auto mb-3">
            <svg className="w-7 h-7 text-white wrench-animate" fill="currentColor" viewBox="0 0 24 24">
              <path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white" style={{fontFamily:"'Rubik',sans-serif"}}>Sanjay Hardware</h1>
          <p className="text-slate-400 text-sm mt-1">Hardware & Sanitary Supplies</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8">
          <h2 className="text-lg font-semibold text-white mb-1">Sign in</h2>
          <p className="text-sm text-slate-400 mb-6">
            {step === "phone" ? "Enter your phone to receive an OTP." : `OTP sent to ${phone}.`}
          </p>
          {step === "phone" ? (
            <form onSubmit={requestOtp} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-slate-300">Phone number</label>
                <input
                  type="tel"
                  placeholder="+91 98765 43210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  required
                  className="px-3 py-2.5 rounded-lg border border-slate-600 bg-slate-700 text-white placeholder-slate-500 text-sm outline-none focus:border-orange-500 transition-colors"
                />
              </div>
              {error && <p className="text-sm text-red-400">{error}</p>}
              <button type="submit" disabled={loading} className="w-full py-2.5 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors disabled:opacity-60 cursor-pointer">
                {loading ? "Sending…" : "Send OTP"}
              </button>
            </form>
          ) : (
            <form onSubmit={verifyOtp} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-slate-300">OTP</label>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="6-digit code"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  maxLength={6}
                  required
                  className="px-3 py-2.5 rounded-lg border border-slate-600 bg-slate-700 text-white placeholder-slate-500 text-sm outline-none focus:border-orange-500 transition-colors text-center text-xl tracking-[0.5em]"
                />
              </div>
              {error && <p className="text-sm text-red-400">{error}</p>}
              <button type="submit" disabled={loading} className="w-full py-2.5 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors disabled:opacity-60 cursor-pointer">
                {loading ? "Verifying…" : "Verify OTP"}
              </button>
              <button type="button" onClick={() => setStep("phone")} className="text-sm text-slate-400 hover:text-white transition-colors text-center cursor-pointer">
                Use a different number
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
