import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  allowedDevOrigins: ["localhost"],
  output: "export",
  trailingSlash: true,
};

export default nextConfig;
