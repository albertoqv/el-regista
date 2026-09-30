import Link from "next/link";
import { Reveal } from "@/app/components/motion";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import type { Player, Season, SimilarPlayerMatch } from "@/lib/api";
import { competitionColor, positionLabel, seasonDisplay } from "@/lib/format";

function compareHref(player: Player, season: Season | null, match: SimilarPlayerMatch): string {
  const params = new URLSearchParams({
    a: String(player.player_id),
    b: String(match.comparison.player2.player_id),
    sbc: match.candidate_season.competition,
    sbl: match.candidate_season.label,
  });
  if (season) {
    params.set("sac", season.competition);
    params.set("sal", season.label);
  } else {
    params.set("sal", "career");
  }
  return `/compare?${params.toString()}`;
}

export function SimilarPlayers({
  player,
  season,
  matches,
}: {
  player: Player;
  season: Season | null;
  matches: SimilarPlayerMatch[];
}) {
  if (matches.length === 0) {
    return (
      <p className="glass rounded-3xl p-6 text-sm text-muted">
        Aún no hay suficientes jugadores comparables.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      {matches.map((match, index) => {
        const other = match.comparison.player2;
        const candidate = match.candidate_season;
        return (
          <Reveal key={`${other.player_id}-${candidate.label}`} delay={index * 0.05}>
            <Link href={compareHref(player, season, match)} className="group relative block">
              <PlayerPortrait
                name={other.name}
                photoUrl={other.photo_url}
                accent={competitionColor(candidate.competition)}
                rounded="rounded-2xl"
                className="aspect-[3/4] transition duration-500 group-hover:-translate-y-1"
              />
              <span className="absolute right-2 top-2 rounded-full bg-black/60 px-2 py-0.5 font-display text-sm font-bold backdrop-blur">
                {match.comparison.similarity_percentage}%
              </span>
              <div className="absolute inset-x-0 bottom-0 p-3">
                <span className="block truncate text-sm font-semibold">{other.name}</span>
                <span className="block truncate text-[11px] text-muted">
                  {positionLabel(other.position)} · {candidate.team ?? candidate.competition}{" "}
                  {seasonDisplay(candidate.label)}
                </span>
              </div>
            </Link>
          </Reveal>
        );
      })}
    </div>
  );
}
