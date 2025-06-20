import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Enable development optimizations
  experimental: {
    // Enable static generation at build time
    optimizePackageImports: ['@radix-ui/react-icons'],
  },
  // Development specific settings
  ...(process.env.NODE_ENV === 'development' && {
    // Force compilation of pages on startup
    compiler: {
      // Remove console logs in production but keep in development
      removeConsole: false,
    },
  }),
};

export default nextConfig;
