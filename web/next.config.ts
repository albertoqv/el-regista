import type { NextConfig } from "next";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEV = process.env.NODE_ENV !== "production";

// Everything is served from this origin (fonts, analytics, the /api proxy); the only
// outside resources are player photos and the visit counter, which posts to the API. Next's inline bootstrap scripts need
// 'unsafe-inline' unless every page is rendered per request with a nonce.
const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${DEV ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https://img.a.transfermarkt.technology",
  "font-src 'self'",
  `connect-src 'self' ${new URL(API_URL).origin}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  "upgrade-insecure-requests",
].join("; ");

const SECURITY_HEADERS = [
  { key: "Content-Security-Policy", value: CONTENT_SECURITY_POLICY },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // The browser talks to the API through the site itself (/api/...): same origin,
  // so no CORS setup is needed whatever domain the web is served from.
  async rewrites() {
    // Ingestion and admin never go through the browser: not proxied at all.
    return [{ source: "/api/:path((?!ingestion|admin|docs|redoc|openapi).*)", destination: `${API_URL}/:path` }];
  },
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
};

export default nextConfig;
