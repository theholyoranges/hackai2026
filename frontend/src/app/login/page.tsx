"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

const features = [
  { title: "Menu Intelligence", desc: "Know what sells, what to cut, and what to promote" },
  { title: "Inventory Control", desc: "Reduce waste and never run out of key ingredients" },
  { title: "Local Demand", desc: "Weather, events, and competitor insights in real time" },
  { title: "Growth Recs", desc: "AI-powered strategies tailored to your restaurant" },
];

export default function LoginPage() {
  const router = useRouter();
  const [id, setId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!id.trim() || !password.trim()) {
      setError("Please enter both fields");
      return;
    }
    setLoading(true);
    setTimeout(() => {
      router.push("/dashboard");
    }, 600);
  };

  return (
    <div className="min-h-screen flex text-white" style={{ backgroundColor: "#14182b" }}>
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-[52%] flex-col justify-between p-12 relative overflow-hidden">

        <div className="relative z-10 flex justify-center mt-12">
          <Image
            src="/logodos.png"
            alt="BistroBrain"
            width={1000}
            height={1000}
            priority
          />
        </div>

        <div className="relative z-10 -mt-4">
          <h1 className="text-4xl font-bold leading-tight tracking-tight">
            Your local restaurant&apos;s<br />
            <span className="bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">
              smartest employee.
            </span>
          </h1>
          <p className="mt-4 text-lg text-slate-400 max-w-md leading-relaxed">
            BistroBrain turns your sales, inventory, and local market data into
            actionable strategies that grow revenue.
          </p>
        </div>

        <div className="relative z-10 grid grid-cols-2 gap-3">
          {features.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-white/[0.06] bg-white/[0.03] backdrop-blur-sm px-4 py-3"
            >
              <p className="text-sm font-semibold text-slate-200">{f.title}</p>
              <p className="text-xs text-slate-500 mt-0.5 leading-snug">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 bg-slate-50">
        <div className="w-full max-w-sm">
          {/* Mobile-only logo */}
          <div className="flex flex-col items-center mb-8 lg:hidden">
            <Image src="/logodos.png" alt="BistroBrain" width={160} height={160} priority />
            <p className="text-slate-500 text-sm mt-2">Your local restaurant&apos;s smartest employee</p>
          </div>

          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900">Welcome back</h2>
            <p className="text-slate-500 text-sm mt-1">Sign in to your restaurant dashboard</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="login-id" className="block text-sm font-medium text-slate-700 mb-1.5">
                Restaurant ID
              </label>
              <input
                id="login-id"
                type="text"
                value={id}
                onChange={(e) => { setId(e.target.value); setError(""); }}
                placeholder="e.g. spicegarden"
                autoComplete="username"
                className="w-full px-4 py-3 rounded-xl border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
              />
            </div>

            <div>
              <label htmlFor="login-pw" className="block text-sm font-medium text-slate-700 mb-1.5">
                Password
              </label>
              <input
                id="login-pw"
                type="password"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(""); }}
                placeholder="Enter your password"
                autoComplete="current-password"
                className="w-full px-4 py-3 rounded-xl border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
              />
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <p className="text-xs text-center text-slate-400 mt-6">
            Protected by enterprise-grade encryption
          </p>
        </div>
      </div>
    </div>
  );
}
