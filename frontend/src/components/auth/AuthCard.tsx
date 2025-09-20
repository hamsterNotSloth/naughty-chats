"use client";
import React, { useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";

type ProfilePatch = { agreeTerms?: boolean; avatarUrl?: string; marketingOptIn?: boolean };

async function patchProfile(apiBase: string, token: string, payload: ProfilePatch) {
  await fetch(`${apiBase}/api/me`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  });
}

// NOTE: Backend no longer accepts local password auth, so this is a UI shell that
// *looks* like a traditional form (to match the reference) but ultimately delegates
// to Entra popup login. If local auth returns in future, wire submit handler accordingly.

export type AuthMode = "signin" | "signup";

interface AuthCardProps {
  mode: AuthMode;
  onSuccess?: () => void;
  className?: string;
}

export const AuthCard: React.FC<AuthCardProps> = ({ mode, onSuccess, className }) => {
  const { login, acquireApiToken } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isSignup = mode === "signup";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (isSignup && password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // We don't actually send email/password to backend currently.
    // Instead we trigger Entra popup. Optional: store email hint.
    try {
      setLoading(true);
      // Pass email as hint if available to improve provider UX
      await login();
      // After login attempt basic onboarding if needed
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      try {
        const token = await acquireApiToken();
        if (token) {
          // Minimal heuristic: send terms agreement if signup flow and user checked the box
          if (isSignup) {
            await patchProfile(apiBase, token, { agreeTerms: true });
          }
        }
      } catch { /* ignore token acquisition errors for UX */ }
      onSuccess?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`w-full max-w-md rounded-xl border border-white/10 bg-neutral-900/80 backdrop-blur p-8 shadow-xl ${className || ""}`}>
      <h2 className="text-2xl font-semibold text-white text-center mb-6">
        {isSignup ? "Create Account" : "Sign In"}
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1">Email</label>
          <input
            type="email"
            className="w-full rounded-md bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-600 text-neutral-100 placeholder-neutral-500"
            placeholder="you@example.com"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1">Password</label>
          <input
            type="password"
            className="w-full rounded-md bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-600 text-neutral-100 placeholder-neutral-500"
            placeholder="••••••••"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
        </div>
        {isSignup && (
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1">Confirm Password</label>
            <input
              type="password"
              className="w-full rounded-md bg-neutral-800 border border-neutral-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-600 text-neutral-100 placeholder-neutral-500"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              required
            />
          </div>
        )}
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
            disabled={loading}
          className="w-full rounded-md bg-gradient-to-r from-pink-500 to-fuchsia-600 hover:from-pink-400 hover:to-fuchsia-500 transition-colors py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {loading ? (isSignup ? "Creating..." : "Signing in...") : isSignup ? "Create Account" : "Sign In"}
        </button>
      </form>
      <div className="relative py-5">
        <div className="absolute inset-0 flex items-center" aria-hidden="true">
          <div className="w-full border-t border-neutral-700" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-neutral-900 px-2 tracking-wide text-neutral-500">or continue with</span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => login()} // Could pass prompt=login or domain_hint for provider-specific
          className="flex items-center justify-center gap-2 rounded-md border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm font-medium text-neutral-200 hover:bg-neutral-750 hover:border-neutral-600 transition-colors"
        >
          <span className="text-neutral-300">Entra</span>
        </button>
        <button
          type="button"
          disabled
          className="flex items-center justify-center gap-2 rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm font-medium text-neutral-500 cursor-not-allowed"
        >
          <span>Discord</span>
        </button>
      </div>
      <p className="mt-6 text-center text-xs text-neutral-500">
        {isSignup ? (
          <>Already have an account? <a href="/signin" className="text-fuchsia-400 hover:underline">Sign In</a></>
        ) : (
          <>Need an account? <a href="/signup" className="text-fuchsia-400 hover:underline">Create one</a></>
        )}
      </p>
      <p className="mt-2 text-center text-[10px] leading-relaxed text-neutral-600">
        We never store your password here; authentication is handled by trusted identity provider.
      </p>
    </div>
  );
};

export default AuthCard;
