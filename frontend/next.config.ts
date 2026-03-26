import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/proxy/:path*',
        destination: 'https://20.197.50.230/:path*',
      },
    ];
  },
};

export default nextConfig;
