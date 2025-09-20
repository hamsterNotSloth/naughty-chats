"use client";
import { useAuth } from "@/components/providers/AuthProvider";
import { useSession } from 'next-auth/react';
import { useState } from "react";

interface SignInButtonProps {
  mode?: "signin" | "signup";
  className?: string;
  label?: string;
}

export function SignInButton({ mode = "signin", className = "", label }: SignInButtonProps) {
  const { login } = useAuth();
  const { data: session, status } = useSession();
  const [clicked, setClicked] = useState(false);
  const isLoading = status === 'loading';
  const user = session?.user;
  const effectiveLabel = label || (mode === "signup" ? "Create Account" : user ? "Account" : "Sign In");

  return (
    <button
      disabled={isLoading || clicked}
      onClick={() => { setClicked(true); void login(); }}
      className={
        `inline-flex items-center justify-center rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-60 disabled:cursor-not-allowed transition ${className}`
      }
      aria-busy={isLoading || clicked}
    >
      {(isLoading || clicked) ? 'Redirecting…' : effectiveLabel}
    </button>
  );
}
