import type { Metadata } from "next";
import "./globals.css";
import Navigation from "@/components/navigation";

export const metadata: Metadata = {
  title: "NaughtyChats - AI Roleplay & Character Discovery",
  description: "Discover and chat with AI characters in immersive roleplay experiences",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-gray-900 text-white min-h-screen font-sans">
        <Navigation />
        {children}
      </body>
    </html>
  );
}
