import type { Season } from "@/lib/api";
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
