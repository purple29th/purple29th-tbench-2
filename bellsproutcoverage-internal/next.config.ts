import type { NextConfig } from 'next';
// On Nest, baseConfig provides internal defaults, XDB tunnels, etc.
const nextConfig: NextConfig = {
  // Standalone output for Tupperware FaaS containerization
  output: 'standalone',
  images: { unoptimized: true },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          // Allow embedding in Unidash via iframe on internal domains only
          { key: 'Content-Security-Policy', value: "frame-ancestors 'self' *.facebook.com *.internalfb.com *.intern.facebook.com" },
        ],
      },
      {
        // /embed route is outside auth group for Unidash iframe — must be SAMEORIGIN
        source: '/embed',
        headers: [
          { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
        ],
      },
    ];
  },
};

export default nextConfig;
