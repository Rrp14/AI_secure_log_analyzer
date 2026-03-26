import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/proxy/:path*',
        destination: 'http://rahulrp.tech:8000/:path*',
      },
    ];
  },
};

export default nextConfig;
