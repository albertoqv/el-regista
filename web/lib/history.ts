import type { PercentileReport, Player, Season } from "@/lib/api";
import type { MetricKey } from "@/lib/metrics";
import { SITE_URL } from "@/lib/site";

/**
 * Past seasons of the big five (2014-2023) from Understat, served as static files
 * from /history (scripts/build_history.py). They never change and never touch the
 * database: Neon's free plan meters every byte read.
 */

/** A season from the static history: `hist:La Liga` + `2017` = La Liga 17/18. */
export const HISTORY_PREFIX = "hist:";

export type HistorySeasonRef = { id: number; name: string; competition: string; year: number; team: string };

export type HistoryRow = {
  id: number;
  name: string;
  team: string;
  position: string;
  games?: number;
  minutes: number;
  goals: number;
  expected_goals: number;
  shots: number;
  assists: number;
  expected_assists: number;
  key_passes: number;
  xg_chain: number;
  xg_buildup: number;
  yellow_cards: number;
  red_cards: number;
};

type HistorySeason = { competition: string; year: number; players: HistoryRow[] };

/** The radar axes Understat has (no passes, dribbles or defending). */
export const HISTORY_METRICS: MetricKey[] = [
  "goals",
  "expected_goals",
  "shots",
  "assists",
  "expected_assists",
  "key_passes",
  "xg_chain",
  "xg_buildup",
];

// A regular's season: below this, per-90 numbers are noise.
const PEER_MINUTES = 900;
const WEEK = 7 * 24 * 3600;

export function normalizedName(name: string): string {
  return name
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();
}

function shardKey(name: string): string {
  const first = normalizedName(name).charAt(0);
  return first >= "a" && first <= "z" ? first : "_";
}

function slug(competition: string): string {
  return competition.toLowerCase().replaceAll(" ", "-");
}

async function getJson<T>(path: string): Promise<T | null> {
  const response = await fetch(`${SITE_URL}${path}`, { next: { revalidate: WEEK } }).catch(() => null);
  return response?.ok ? ((await response.json()) as T) : null;
}

/**
 * A player's seasons in the history, by name. Two different Understat players with
 * the same name are ambiguous: nothing is returned rather than mixing them.
 */
export async function historySeasons(name: string): Promise<HistorySeasonRef[]> {
  const shard = await getJson<Record<string, HistorySeasonRef[]>>(`/history/index/${shardKey(name)}.json`);
  const seasons = shard?.[normalizedName(name)] ?? [];
  if (new Set(seasons.map((season) => season.id)).size > 1) return [];
  return [...seasons].sort((a, b) => b.year - a.year);
}

/** The player's row in that league season, with everyone else in it. */
export async function historySeason(
  competition: string,
  year: number,
  name: string,
): Promise<{ row: HistoryRow; peers: HistoryRow[] } | null> {
  const [refs, season] = await Promise.all([
    historySeasons(name),
    getJson<HistorySeason>(`/history/${slug(competition)}-${year}.json`),
  ]);
  const ref = refs.find((entry) => entry.competition === competition && entry.year === year);
  const row = season?.players.find((player) => player.id === ref?.id);
  return row && season ? { row, peers: season.players } : null;
}

function per90(row: HistoryRow, key: MetricKey): number {
  const value = row[key as keyof HistoryRow];
  return row.minutes && typeof value === "number" ? (value * 90) / row.minutes : 0;
}

/**
 * Percentiles against the regulars of his position in that league season, in the
 * same shape as the API's report (radar and percentile bars read it as is).
 */
export function historyPercentiles(
  row: HistoryRow,
  peers: HistoryRow[],
  competition: string,
  year: number,
): PercentileReport {
  const group = peers.filter((peer) => peer.position === row.position && peer.minutes >= PEER_MINUTES);
  const pool = group.length ? group : [row];
  const metrics = Object.fromEntries(
    HISTORY_METRICS.map((key) => {
      const mine = per90(row, key);
      const below = pool.filter((peer) => per90(peer, key) <= mine).length;
      return [key, { per_90: mine, percentile: Math.round((below / pool.length) * 100) }];
    }),
  );
  return {
    competition,
    season_label: String(year),
    position: row.position,
    peer_count: pool.length,
    minimum_minutes: PEER_MINUTES,
    metrics,
  };
}

/** The history seasons as season picker entries (`hist:La Liga` + year). */
export function historySeasonEntries(refs: HistorySeasonRef[]): Season[] {
  return refs.map((ref) => ({
    competition: `${HISTORY_PREFIX}${ref.competition}`,
    label: String(ref.year),
    team: ref.team,
  }));
}

/** The player with that season's numbers (Understat has no passes or defending). */
export function historyPlayer(player: Player, row: HistoryRow): Player {
  return {
    ...player,
    goals: row.goals,
    assists: row.assists,
    shots: row.shots,
    shots_on_target: 0,
    expected_goals: row.expected_goals,
    passes_completed: 0,
    passes_attempted: 0,
    key_passes: row.key_passes,
    dribbles_completed: 0,
    dribbles_attempted: 0,
    tackles_won: 0,
    interceptions: 0,
    fouls_committed: 0,
    fouls_won: 0,
    yellow_cards: row.yellow_cards,
    red_cards: row.red_cards,
    minutes_played: row.minutes,
    expected_assists: row.expected_assists,
    xg_chain: row.xg_chain,
    xg_buildup: row.xg_buildup,
  };
}
