import type { LeaderMetric } from "@/lib/api";
import { COMPETITIONS } from "@/lib/format";

/** League pages with readable URLs: /ranking/laliga/goleadores. */
export const RANKING_LEAGUES: { slug: string; competition: (typeof COMPETITIONS)[number]; name: string }[] = [
  { slug: "laliga", competition: "La Liga", name: "LaLiga" },
  { slug: "premier-league", competition: "Premier League", name: "la Premier League" },
  { slug: "serie-a", competition: "Serie A", name: "la Serie A" },
  { slug: "bundesliga", competition: "Bundesliga", name: "la Bundesliga" },
  { slug: "ligue-1", competition: "Ligue 1", name: "la Ligue 1" },
];

/** Only metrics the current season has (dribbles and tackles stopped in 24/25). */
export const RANKING_METRICS: { slug: string; metric: LeaderMetric; title: string; label: string; unit: string }[] = [
  { slug: "goleadores", metric: "goals", title: "Goleadores", label: "Goles", unit: "goles" },
  { slug: "asistentes", metric: "assists", title: "Asistentes", label: "Asistencias", unit: "asistencias" },
  { slug: "xg", metric: "expected_goals", title: "Más xG", label: "xG", unit: "xG" },
  { slug: "xa", metric: "expected_assists", title: "Más xA", label: "xA", unit: "xA" },
  { slug: "tiros", metric: "shots", title: "Más tiros", label: "Tiros", unit: "tiros" },
  { slug: "pases-clave", metric: "key_passes", title: "Más pases clave", label: "Pases clave", unit: "pases clave" },
];

export function findRanking(liga: string, metrica: string) {
  const league = RANKING_LEAGUES.find((entry) => entry.slug === liga);
  const metric = RANKING_METRICS.find((entry) => entry.slug === metrica);
  return league && metric ? { league, metric } : null;
}

export function rankingHref(liga: string, metrica: string): string {
  return `/ranking/${liga}/${metrica}`;
}
