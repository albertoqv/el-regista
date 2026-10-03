const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
// A page that breaks in a loop must not flood the API: a few distinct errors per visit.
const MAX_PER_PAGE_LOAD = 5;
const sent = new Set<string>();

/** Sends a browser error to the admin panel (no cookies, nothing read back). */
export function reportError(message: string): void {
  if (typeof window === "undefined" || !message || sent.has(message) || sent.size >= MAX_PER_PAGE_LOAD) return;
  if (window.location.pathname.startsWith("/admin")) return;
  sent.add(message);
  fetch(`${API_URL}/metrics/error`, {
    method: "POST",
    body: JSON.stringify({ message: message.slice(0, 300), path: window.location.pathname }),
    headers: { "Content-Type": "text/plain" },
    keepalive: true,
    mode: "no-cors",
  }).catch(() => {});
}
