import type { CompetitionLine, Player, Season } from "@/lib/api";
import { sortSeasonsByRecency } from "@/lib/format";

export const CAREER = "career";

/**
 * Season picked in the URL; without one, the player's most recent season.
 * `null` means the whole career.
 */
export function resolveSeason(
  seasons: Season[],
  competition: string | undefined,
  label: string | undefined,
): Season | null {
  if (label === CAREER) return null;
  if (competition && label) {
    return (
      seasons.find((season) => season.competition === competition && season.label === label) ?? {
        competition,
        label,
      }
    );
  }
  return sortSeasonsByRecency(seasons)[0] ?? null;
}

/** A whole club season, every competition added up (league, Europe, cups). */
export const ALL_COMPETITIONS = "Todas las competiciones";

/** Club seasons of a player's competition lines, newest first. */
export function clubSeasons(lines: CompetitionLine[]): Season[] {
  const labels = [...new Set(lines.filter((line) => line.kind !== "national").map((line) => line.season_label))];
  return labels
    .sort((a, b) => Number(b) - Number(a))
    .map((label) => ({ competition: ALL_COMPETITIONS, label, team: mainTeam(lines, label) }));
}

function mainTeam(lines: CompetitionLine[], label: string): string | null {
  const club = lines.filter((line) => line.kind !== "national" && line.season_label === label);
  return club.sort((a, b) => b.minutes_played - a.minutes_played)[0]?.team ?? null;
}

/**
 * The player with one club season's numbers, every competition added up. Only what
 * every competition has (games, goals, assists, minutes, cards): the rest stays 0.
 */
export function playerInClubSeason(player: Player, lines: CompetitionLine[], label: string): Player {
  const club = lines.filter((line) => line.kind !== "national" && line.season_label === label);
  const add = (key: "goals" | "assists" | "minutes_played" | "yellow_cards" | "red_cards") =>
    club.reduce((total, line) => total + line[key], 0);
  return {
    ...player,
    goals: add("goals"),
    assists: add("assists"),
    minutes_played: add("minutes_played"),
    yellow_cards: add("yellow_cards"),
    red_cards: add("red_cards"),
    shots: 0,
    shots_on_target: 0,
    expected_goals: 0,
    passes_completed: 0,
    passes_attempted: 0,
    key_passes: 0,
    dribbles_completed: 0,
    dribbles_attempted: 0,
    tackles_won: 0,
    interceptions: 0,
    fouls_committed: 0,
    fouls_won: 0,
    expected_assists: 0,
    xg_chain: 0,
    xg_buildup: 0,
  };
}
