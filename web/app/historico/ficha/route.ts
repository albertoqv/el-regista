import { redirect } from "next/navigation";
import { listPlayers } from "@/lib/api";
import { HISTORY_PREFIX, normalizedName } from "@/lib/history";

// From 2024 on the season lives in the database, with its detailed metrics.
const FIRST_DATABASE_YEAR = 2024;

/**
 * A history season opens the player's page when we have him (one player with
 * exactly that name); otherwise his page from the static history.
 */
export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const name = params.get("nombre") ?? "";
  const competition = params.get("liga") ?? "";
  const year = Number(params.get("anio"));
  const fallback = `/historico/jugador/${encodeURIComponent(params.get("j") ?? "")}`;
  const found = name ? await listPlayers({ q: name, limit: 10 }).catch(() => []) : [];
  const same = found.filter((player) => normalizedName(player.name) === normalizedName(name));
  if (same.length !== 1) redirect(fallback);
  const season =
    competition && year
      ? `?sc=${encodeURIComponent(year >= FIRST_DATABASE_YEAR ? competition : `${HISTORY_PREFIX}${competition}`)}&sl=${year}`
      : "";
  redirect(`/players/${same[0].player_id}${season}`);
}
