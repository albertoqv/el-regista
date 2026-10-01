import Link from "next/link";
import type { Season } from "@/lib/api";
import { competitionColor, seasonDisplay } from "@/lib/format";
import { CAREER } from "@/lib/seasons";

function pill(active: boolean): string {
  return `flex shrink-0 items-center gap-2 rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
    active
      ? "border-white/30 bg-white text-bg"
      : "border-line text-muted hover:border-line-strong hover:text-ink"
  }`;
}

export function SeasonSelector({
  playerId,
  seasons,
  selected,
}: {
  playerId: number;
  seasons: Season[];
  selected: Season | null;
}) {
  return (
    <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
      {seasons.map((season) => {
        const active =
          selected?.competition === season.competition && selected?.label === season.label;
        return (
          <Link
            key={`${season.competition}-${season.label}`}
            href={`/players/${playerId}?sc=${encodeURIComponent(season.competition)}&sl=${encodeURIComponent(season.label)}`}
            className={pill(active)}
            scroll={false}
          >
            <span
              className="h-1.5 w-1.5 rounded-full"
              style={{ background: competitionColor(season.competition) }}
            />
            {seasonDisplay(season.label)} · {season.team ?? season.competition}
          </Link>
        );
      })}
      <Link href={`/players/${playerId}?sl=${CAREER}`} className={pill(selected === null)} scroll={false}>
        Carrera completa
      </Link>
    </div>
  );
}
