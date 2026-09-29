import Link from "next/link";
import type { Season } from "@/lib/api";

function pillClasses(active: boolean): string {
  return active
    ? "rounded-full bg-[#2a78d6] px-3 py-1 text-sm font-medium text-white"
    : "rounded-full border border-zinc-300 px-3 py-1 text-sm font-medium text-zinc-700 hover:border-zinc-500 dark:border-zinc-700 dark:text-zinc-300";
}

export function SeasonSelector({
  playerId,
  seasons,
  selected,
}: {
  playerId: number;
  seasons: Season[];
  selected?: Season;
}) {
  if (seasons.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      <Link href={`/players/${playerId}`} className={pillClasses(!selected)}>
        Carrera
      </Link>
      {seasons.map((season) => {
        const isSelected =
          selected?.competition === season.competition &&
          selected?.label === season.label;
        return (
          <Link
            key={`${season.competition}-${season.label}`}
            href={`/players/${playerId}?sc=${encodeURIComponent(season.competition)}&sl=${encodeURIComponent(season.label)}`}
            className={pillClasses(isSelected)}
          >
            {season.competition} {season.label}
          </Link>
        );
      })}
    </div>
  );
}
