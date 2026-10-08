import { historySeasons } from "@/lib/history";

/** A player's seasons in the static history, for the duel's season picker. */
export async function GET(request: Request) {
  const name = new URL(request.url).searchParams.get("nombre") ?? "";
  const seasons = name ? await historySeasons(name) : [];
  return Response.json(seasons, { headers: { "Cache-Control": "public, s-maxage=604800" } });
}
