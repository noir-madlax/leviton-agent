import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
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
  // Rewrites for PostHog API proxying
  async rewrites() {
    return [
      {
        source: '/ingest/static/:path*',
        destination: 'https://us-assets.i.posthog.com/static/:path*',
      },
      {
        source: '/ingest/:path*',
        destination: 'https://us.i.posthog.com/:path*',
      },
      {
        source: '/ingest/decide',
        destination: 'https://us.i.posthog.com/decide',
      },
    ];
  },
  // This is required to support PostHog trailing slash API requests
  skipTrailingSlashRedirect: true,
};

export default nextConfig;
