import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Keep tracing rooted on this product when parent lockfiles exist
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
