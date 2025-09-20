"use client";
import AuthCard from "@/components/auth/AuthCard";
import { Layout } from "@/components/layout/Layout";

export default function SignUpPage() {
  return (
    <Layout>
      <div className="min-h-[70vh] flex items-center justify-center px-4">
        <AuthCard mode="signup" />
      </div>
    </Layout>
  );
}