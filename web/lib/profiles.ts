import { HISTORY_METRICS, HISTORY_VERSION, normalizedName } from "@/lib/history";
import type { MetricKey } from "@/lib/metrics";
import { SITE_URL } from "@/lib/site";

/**
 * Every regular season (≥900') of the big five since 2014 with its percentiles
 * against the same line in that league season (scripts/build_history.py writes
 * /history/profiles). Twins across eras, best seasons and a player's peak read
 * these three static files: nothing touches the database.
 */

export const LINES = ["Forward", "Midfielder", "Defender"] as const;
export type Line = (typeof LINES)[number];

export const LINE_LABELS: Record<Line, string> = {
  Forward: "Delanteros",
  Midfielder: "Centrocampistas",
  Defender: "Defensas",
};

export type Profile = {
  id: number;
  name: string;
  team: string;
  competition: string;
  year: number;
  minutes: number;
  line: Line;
  totals: Record<MetricKey, number>;
  percentiles: Record<MetricKey, number>;
};

type ProfileFile = { fields: string[]; competitions: string[]; rows: (string | number)[][] };

const WEEK = 7 * 24 * 3600;

async function loadLine(line: Line): Promise<Profile[]> {
  const response = await fetch(`${SITE_URL}/history/profiles/${line.toLowerCase()}.json?v=${HISTORY_VERSION}`, {
    next: { revalidate: WEEK },
  }).catch(() => null);
  if (!response?.ok) return [];
  const file = (await response.json()) as ProfileFile;
  const at = (name: string) => file.fields.indexOf(name);
  return file.rows.map((row) => ({
    id: row[at("id")] as number,
    name: row[at("name")] as string,
    team: row[at("team")] as string,
    competition: file.competitions[row[at("competition")] as number],
    year: row[at("year")] as number,
    minutes: row[at("minutes")] as number,
    line,
    totals: Object.fromEntries(HISTORY_METRICS.map((key) => [key, row[at(key)] as number])) as Record<MetricKey, number>,
    percentiles: Object.fromEntries(HISTORY_METRICS.map((key) => [key, row[at(`p_${key}`)] as number])) as Record<
      MetricKey,
      number
    >,
  }));
}

export async function loadProfiles(lines: readonly Line[] = LINES): Promise<Profile[]> {
  return (await Promise.all(lines.map(loadLine))).flat();
}

/** `la-liga-2015`: one season of one player in a URL. */
export function seasonKey(profile: Pick<Profile, "competition" | "year">): string {
  return `${profile.competition.toLowerCase().replaceAll(" ", "-")}-${profile.year}`;
}

/** How good a season was by Understat's metrics: the mean of its percentiles. */
export function seasonScore(profile: Profile): number {
  return Math.round(HISTORY_METRICS.reduce((sum, key) => sum + profile.percentiles[key], 0) / HISTORY_METRICS.length);
}

/** 100 minus the mean gap between percentiles, as the twins of the season do. */
export function similarity(a: Profile, b: Profile): number {
  const gap = HISTORY_METRICS.reduce((sum, key) => sum + Math.abs(a.percentiles[key] - b.percentiles[key]), 0);
  return Math.round(100 - gap / HISTORY_METRICS.length);
}

export function latestYear(profiles: Profile[]): number {
  return profiles.reduce((max, profile) => Math.max(max, profile.year), 0);
}

export type Era = "hoy" | "antes";

/**
 * The seasons most like `target` from the same line: from the latest finished
 * season ("hoy") or from any earlier one ("antes"), one season per player.
 */
export function eraTwins(target: Profile, profiles: Profile[], era: Era, limit = 12) {
  const latest = latestYear(profiles);
  const best = new Map<number, { profile: Profile; similarity: number }>();
  for (const profile of profiles) {
    if (profile.line !== target.line || profile.id === target.id) continue;
    if (era === "hoy" ? profile.year !== latest : profile.year >= latest) continue;
    const score = similarity(target, profile);
    const current = best.get(profile.id);
    if (!current || score > current.similarity) best.set(profile.id, { profile, similarity: score });
  }
  return [...best.values()].sort((a, b) => b.similarity - a.similarity).slice(0, limit);
}

/** The player's seasons, oldest first. */
export function seasonsOf(id: number, profiles: Profile[]): Profile[] {
  return profiles.filter((profile) => profile.id === id).sort((a, b) => a.year - b.year);
}

export function bestSeason(seasons: Profile[]): Profile | null {
  return seasons.reduce<Profile | null>(
    (best, season) => (!best || seasonScore(season) > seasonScore(best) ? season : best),
    null,
  );
}

/** Players whose name contains every word typed, without accents. */
export function searchProfiles(query: string, profiles: Profile[], limit = 8) {
  const words = normalizedName(query).split(/\s+/).filter(Boolean);
  if (words.length === 0) return [];
  const players = new Map<number, Profile[]>();
  for (const profile of profiles) {
    const name = normalizedName(profile.name);
    if (words.every((word) => name.includes(word))) {
      players.set(profile.id, [...(players.get(profile.id) ?? []), profile]);
    }
  }
  return [...players.values()]
    .map((seasons) => {
      const sorted = [...seasons].sort((a, b) => a.year - b.year);
      const last = sorted[sorted.length - 1];
      return { id: last.id, name: last.name, team: last.team, first: sorted[0].year, last: last.year, seasons: sorted.length };
    })
    .sort((a, b) => b.seasons - a.seasons)
    .slice(0, limit);
}

/**
 * A season picked in a URL: `2097` (his best season) or `2097:la-liga-2015`.
 * Returns his seasons and the one picked, or null when the id is unknown.
 */
export function pickSeason(value: string | undefined, profiles: Profile[]) {
  const [rawId, key] = (value ?? "").split(":");
  const seasons = seasonsOf(Number(rawId), profiles);
  const profile = seasons.find((season) => seasonKey(season) === key) ?? bestSeason(seasons);
  return profile ? { seasons, profile } : null;
}

export function pickValue(profile: Profile): string {
  return `${profile.id}:${seasonKey(profile)}`;
}

/** Whom he resembles most in the other era: his latest season against the
 * latest finished one, or, if that is his, against every earlier season. */
export function closestAcrossEras(seasons: Profile[], profiles: Profile[]) {
  const last = seasons[seasons.length - 1];
  if (!last) return null;
  const era: Era = last.year === latestYear(profiles) ? "antes" : "hoy";
  const [twin] = eraTwins(last, profiles, era, 1);
  return twin ? { season: last, era, ...twin } : null;
}

export function seasonName(profile: Pick<Profile, "competition" | "year">): string {
  return `${profile.competition} ${String(profile.year).slice(2)}/${String(profile.year + 1).slice(2)}`;
}
