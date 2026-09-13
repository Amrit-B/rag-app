import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" },
      { source: "/auth/:path*", destination: "http://127.0.0.1:8000/auth/:path*" },
      { source: "/rag/:path*", destination: "http://127.0.0.1:8000/rag/:path*" },
      { source: "/admin/:path*", destination: "http://127.0.0.1:8000/admin/:path*" },
    ];
  },
};

export default nextConfig;
