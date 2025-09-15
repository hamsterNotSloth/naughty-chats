'use client';

import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { useAuth } from '@/components/providers/AuthProvider';

// Sign-in page now delegates all auth to Entra External ID (B2C) via MSAL.
// Email/password & social providers (Google/Twitter/Discord) are surfaced on the hosted user flow page.

export default function SignInPage() {
  const { login } = useAuth();

  return (
    <Layout>
      <div className="min-h-[calc(100vh-4rem)] flex">
        {/* Left side - Form */}
        <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8">
          <div className="max-w-md w-full space-y-8">
            <div>
              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Welcome back
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                Don&apos;t have an account?{' '}
                <Link
                  href="/signup"
                  className="font-medium text-purple-600 hover:text-purple-500"
                >
                  Sign up for free
                </Link>
              </p>
            </div>
            
            <div className="mt-8 space-y-6">
              <p className="text-sm text-gray-600 text-center">
                Sign in is handled by our secure identity provider. You can use email/password or configured social accounts (Google, Twitter, Discord) once enabled.
              </p>
              <button
                onClick={() => login()}
                className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                Continue with Secure Sign In
              </button>
              <p className="text-xs text-gray-400 text-center">
                You will be redirected to the hosted sign-in page.
              </p>
            </div>
          </div>
        </div>

        {/* Right side - Artwork */}
        <div className="hidden lg:block relative w-0 flex-1">
          <div className="absolute inset-0 h-full w-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
            <div className="text-center text-white">
              <h3 className="text-3xl font-bold mb-4">Welcome to Naughty Chats</h3>
              <p className="text-lg opacity-90 max-w-md">
                Join thousands of users chatting with amazing AI characters. 
                Create your own stories and explore unlimited possibilities.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}