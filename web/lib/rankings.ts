import type { LeaderMetric } from "@/lib/api";

export type RankingLeague = {
  slug: string;
  competition: string;
  name: string;
  /** Only goals and assists (Transfermarkt): no xG, shots or key passes. */
  basic?: boolean;
  /** Second tiers get their own group in the filter. */
  second?: boolean;
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
  { slug: "bundesliga-austriaca", competition: "Austrian Bundesliga", name: "la Bundesliga austriaca", basic: true },
  { slug: "superliga-suiza", competition: "Swiss Super League", name: "la Superliga suiza", basic: true },
  { slug: "ekstraklasa", competition: "Ekstraklasa", name: "la Ekstraklasa", basic: true },
  { slug: "liga-checa", competition: "Czech First League", name: "la liga checa", basic: true },
  { slug: "hnl-croata", competition: "Croatian HNL", name: "la HNL croata", basic: true },
  { slug: "superliga-rumana", competition: "Romanian Superliga", name: "la Superliga rumana", basic: true },
  { slug: "superliga-serbia", competition: "Serbian SuperLiga", name: "la Superliga serbia", basic: true },
  { slug: "saudi-pro-league", competition: "Saudi Pro League", name: "la Saudi Pro League", basic: true },
  { slug: "liga-mx", competition: "Liga MX", name: "la Liga MX", basic: true },
  { slug: "a-league", competition: "A-League", name: "la A-League", basic: true },
  { slug: "championship", competition: "Championship", name: "la Championship", basic: true, second: true },
  { slug: "league-one", competition: "League One", name: "la League One", basic: true, second: true },
  { slug: "segunda-division", competition: "Segunda División", name: "la Segunda División", basic: true, second: true },
  { slug: "serie-b", competition: "Serie B", name: "la Serie B", basic: true, second: true },
  { slug: "2-bundesliga", competition: "2. Bundesliga", name: "la 2. Bundesliga", basic: true, second: true },
  { slug: "3-liga", competition: "3. Liga", name: "la 3. Liga", basic: true, second: true },
  { slug: "ligue-2", competition: "Ligue 2", name: "la Ligue 2", basic: true, second: true },
  { slug: "eerste-divisie", competition: "Eerste Divisie", name: "la Eerste Divisie", basic: true, second: true },
  { slug: "liga-portugal-2", competition: "Liga Portugal 2", name: "la Liga Portugal 2", basic: true, second: true },
];

/** The filter's groups, in order. */
export const LEAGUE_GROUPS = [
  { label: "5 grandes", leagues: RANKING_LEAGUES.filter((league) => !league.basic) },
  { label: "Otras ligas", leagues: RANKING_LEAGUES.filter((league) => league.basic && !league.second) },
  { label: "Segundas", leagues: RANKING_LEAGUES.filter((league) => league.second) },
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
