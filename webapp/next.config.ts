import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // produce a static export so Azure Static Web Apps can host the built files
  output: "export",
};

export default nextConfig;
