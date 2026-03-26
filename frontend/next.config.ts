import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/proxy/:path*',
        destination: 'https://rahulrp.tech:8000/:path*',
      },
    ];
  },
};

export default nextConfig;
