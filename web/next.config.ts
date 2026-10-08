import type { NextConfig } from "next";

// The browser only talks to Next.js; /api/* is proxied to the FastAPI backend.
const API = process.env.API_URL ?? "http://127.0.0.1:8000";

const config: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default config;
