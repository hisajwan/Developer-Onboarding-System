import type { NextConfig } from "next";
import { BACKEND_URL } from "./src/config/backend";

const nextConfig: NextConfig = {
  experimental: {
    // Default is 30 s; indexing a document with real models can take minutes.
    proxyTimeout: 300_000,
  },
  // The browser only ever talks to this origin; the backend URL stays server-side.
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${BACKEND_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
