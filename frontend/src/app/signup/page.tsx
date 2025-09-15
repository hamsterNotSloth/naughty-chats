"use client";

import { Layout } from '@/components/layout/Layout';
import { useAuth } from '@/components/providers/AuthProvider';

export default function SignUpPage() {
  const { login } = useAuth();
  return (
    <Layout>
      <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">Create your account</h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              We use a secure identity provider. Email/password and configured social providers are offered there.
            </p>
          </div>
          <div className="space-y-6">
            <button
              onClick={() => login()}
              className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
            >
              Continue to Secure Sign Up
            </button>
            <p className="text-xs text-center text-gray-400">Redirecting takes you to the hosted sign-up/sign-in flow.</p>
          </div>
        </div>
      </div>
    </Layout>
  );
}