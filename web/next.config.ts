import type { NextConfig } from "next";

// The browser only talks to Next.js; /api/* is proxied to the FastAPI backend.
const API = process.env.API_URL ?? "http://127.0.0.1:8000";

const config: NextConfig = {
  // Agent runs (reader, grouping, matcher) on a new RFP make hundreds of model calls and can take many minutes;
  // the default proxy wait (about 30 s) cut them off with "socket hang up" while the API kept working.
  // ponytail: a long-held request; run agents as background jobs with progress polling if this becomes a problem.
  experimental: { proxyTimeout: 30 * 60 * 1000 },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default config;
