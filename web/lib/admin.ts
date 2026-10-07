// Cookie holding the signed admin session (httpOnly, only sent to /admin).
export const ADMIN_COOKIE = "ts_admin";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type DailyVisits = { day: string; views: number; visitors: number };
export type RankedCount = { name: string; views: number; visitors: number };

export type AdminDashboard = {
  days: number;
  views_today: number;
  visitors_today: number;
  views_period: number;
  visitors_period: number;
  daily: DailyVisits[];
  top_pages: RankedCount[];
  top_referrers: RankedCount[];
  hosting: {
    period_start: string;
    period_end: string;
    current_dollars: number;
    estimated_dollars: number | null;
    line_items: Record<string, number>;
    usage_limit_dollars: number | null;
  } | null;
  hosting_error: string | null;
  hosting_configured: boolean;
  database_usage: {
    period_start: string;
    period_end: string;
    transfer_bytes: number;
    transfer_limit_bytes: number;
    compute_seconds: number;
    written_bytes: number;
  } | null;
  database_usage_error: string | null;
  database_usage_configured: boolean;
  data: Record<string, number>;
  client_errors: { message: string; path: string; count: number; last_seen: string }[];
  data_quality: { missing_results: string[]; goal_mismatches: string[]; latest_result: string | null };
  api: {
    since: string;
    requests: number;
    server_errors: number;
    p50_ms: number;
    p95_ms: number;
    top_routes: [string, number][];
    slow_routes: [string, number][];
  };
};

/** Trades the key for a signed, expiring session token. */
export async function openAdminSession(key: string): Promise<string | "unauthorized" | "blocked" | null> {
  try {
    const response = await fetch(`${API_URL}/admin/session`, {
      method: "POST",
      headers: { "X-Ingestion-Key": key },
      cache: "no-store",
    });
    if (response.status === 401) return "unauthorized";
    if (response.status === 429) return "blocked";
    if (!response.ok) return null;
    return ((await response.json()) as { token: string }).token;
  } catch {
    return null;
  }
}

export async function getAdminDashboard(
  session: string,
  days = 30,
): Promise<AdminDashboard | "unauthorized" | "unavailable"> {
  try {
    const response = await fetch(`${API_URL}/admin/dashboard?days=${days}`, {
      headers: { Authorization: `Bearer ${session}` },
      cache: "no-store",
    });
    if (response.status === 401) return "unauthorized";
    if (!response.ok) return "unavailable";
    return (await response.json()) as AdminDashboard;
  } catch {
    return "unavailable";
  }
}
