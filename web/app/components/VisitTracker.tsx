"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Counts one page view per navigation. No cookies and no IP stored: the API keeps
 * only a daily-rotating hash, so there is no consent banner to show.
 */
export function VisitTracker() {
  const pathname = usePathname();
  const lastPath = useRef<string | null>(null);

  useEffect(() => {
    // Once per navigation, even if React runs the effect twice.
    if (!pathname || pathname === lastPath.current || pathname.startsWith("/admin")) return;
    // The external referrer only matters for the page people landed on.
    const referrer = lastPath.current === null ? document.referrer : "";
    lastPath.current = pathname;
    // text/plain keeps it a "simple" request: no CORS preflight, one round trip.
    fetch(`${API_URL}/metrics/visit`, {
      method: "POST",
      body: JSON.stringify({ path: pathname, referrer }),
      headers: { "Content-Type": "text/plain" },
      keepalive: true,
    }).catch(() => {});
  }, [pathname]);

  return null;
}
