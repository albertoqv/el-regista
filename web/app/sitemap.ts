import type { MetadataRoute } from "next";
import {
  getLeagueTable,
  getPredictions,
  listPlayers,
  listSeasonLeaders,
  type Forecast,
  type LeaderMetric,
  type Player,
  type SeasonLeader,
  type TableRow,
} from "@/lib/api";
import { COMPETITIONS, currentSeasonStartYear } from "@/lib/format";
import { rankingHref, rankingPages } from "@/lib/rankings";
import { SITE_URL as SITE } from "@/lib/site";

// Rebuilt every hour: new matches and players appear without a deploy.
export const revalidate = 3600;

type Frequency = "daily" | "weekly" | "monthly";

const PAGES: { path: string; changeFrequency: Frequency; priority: number }[] = [
  { path: "", changeFrequency: "daily", priority: 1 },
  { path: "/predicciones", changeFrequency: "daily", priority: 0.9 },
  { path: "/predicciones/historial", changeFrequency: "weekly", priority: 0.8 },
  { path: "/en-racha", changeFrequency: "daily", priority: 0.8 },
  { path: "/ranking", changeFrequency: "daily", priority: 0.8 },
  { path: "/buscar", changeFrequency: "weekly", priority: 0.7 },
  { path: "/gemelos", changeFrequency: "weekly", priority: 0.9 },
  { path: "/equipos", changeFrequency: "daily", priority: 0.8 },
  { path: "/explorar", changeFrequency: "weekly", priority: 0.7 },
  { path: "/compare", changeFrequency: "weekly", priority: 0.7 },
  { path: "/como-funciona", changeFrequency: "monthly", priority: 0.5 },
  { path: "/juego-responsable", changeFrequency: "monthly", priority: 0.3 },
  { path: "/aviso-legal", changeFrequency: "monthly", priority: 0.2 },
  { path: "/privacidad", changeFrequency: "monthly", priority: 0.2 },
];

/** Players worth indexing: the season's leaders in each league plus the all-time top scorers. */
const PLAYER_METRICS: LeaderMetric[] = ["goals", "assists", "expected_goals", "key_passes"];

async function notablePlayerIds(season: number): Promise<number[]> {
  const boards = await Promise.all([
    ...COMPETITIONS.flatMap((competition) =>
      PLAYER_METRICS.map((metric) =>
        listSeasonLeaders(season, { metric, competition, limit: 50 }).catch((): SeasonLeader[] => []),
      ),
    ),
    listPlayers({ sort: "goals", limit: 200 }).catch((): Player[] => []),
  ]);
  return [...new Set(boards.flat().map((player) => player.player_id))];
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const season = currentSeasonStartYear();
  const [playerIds, tables, forecasts] = await Promise.all([
    notablePlayerIds(season),
    Promise.all(
      COMPETITIONS.map((competition) =>
        getLeagueTable(String(season), competition).catch((): TableRow[] => []),
      ),
    ),
    getPredictions(14).catch((): Forecast[] => []),
  ]);

  const entry = (path: string, changeFrequency: Frequency, priority: number) => ({
    url: `${SITE}${path}`,
    lastModified: now,
    changeFrequency,
    priority,
  });

  return [
    ...PAGES.map((page) => entry(page.path, page.changeFrequency, page.priority)),
    ...rankingPages().map(({ league, metric }) => entry(rankingHref(league.slug, metric.slug), "daily", 0.7)),
    ...tables
      .flat()
      .map((row) =>
        entry(
          `/equipos/${encodeURIComponent(row.team)}?liga=${encodeURIComponent(row.competition)}`,
          "daily",
          0.6,
        ),
      ),
    ...forecasts.map((forecast) => entry(`/predicciones/${forecast.match_id}`, "daily", 0.6)),
    ...playerIds.map((id) => entry(`/players/${id}`, "weekly", 0.5)),
  ];
}
