import type { LeaderMetric } from "@/lib/api";

export type RankingLeague = {
  slug: string;
  competition: string;
  name: string;
  /** Only goals and assists (Transfermarkt): no xG, shots or key passes. */
  basic?: boolean;
};

/** League pages with readable URLs: /ranking/laliga/goleadores. */
export const RANKING_LEAGUES: RankingLeague[] = [
  { slug: "laliga", competition: "La Liga", name: "LaLiga" },
  { slug: "premier-league", competition: "Premier League", name: "la Premier League" },
  { slug: "serie-a", competition: "Serie A", name: "la Serie A" },
  { slug: "bundesliga", competition: "Bundesliga", name: "la Bundesliga" },
  { slug: "ligue-1", competition: "Ligue 1", name: "la Ligue 1" },
  { slug: "liga-portugal", competition: "Liga Portugal", name: "la Liga Portugal", basic: true },
  { slug: "eredivisie", competition: "Eredivisie", name: "la Eredivisie", basic: true },
  { slug: "super-lig", competition: "Süper Lig", name: "la Süper Lig", basic: true },
  { slug: "jupiler-pro-league", competition: "Jupiler Pro League", name: "la Jupiler Pro League", basic: true },
  { slug: "premiership-escocesa", competition: "Scottish Premiership", name: "la Premiership escocesa", basic: true },
  { slug: "superliga-griega", competition: "Greek Super League", name: "la Superliga griega", basic: true },
  { slug: "superliga-danesa", competition: "Danish Superliga", name: "la Superliga danesa", basic: true },
  { slug: "liga-ucraniana", competition: "Ukrainian Premier League", name: "la liga ucraniana", basic: true },
  { slug: "liga-rusa", competition: "Russian Premier League", name: "la liga rusa", basic: true },
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

const BASIC_METRICS = new Set(["goleadores", "asistentes"]);

export function metricsFor(league: RankingLeague) {
  return league.basic ? RANKING_METRICS.filter((metric) => BASIC_METRICS.has(metric.slug)) : RANKING_METRICS;
}

/** Every page there is: each league with the metrics it has. */
export function rankingPages() {
  return RANKING_LEAGUES.flatMap((league) => metricsFor(league).map((metric) => ({ league, metric })));
}

export function findRanking(liga: string, metrica: string) {
  return rankingPages().find((page) => page.league.slug === liga && page.metric.slug === metrica) ?? null;
}

export function rankingHref(liga: string, metrica: string): string {
  return `/ranking/${liga}/${metrica}`;
}
