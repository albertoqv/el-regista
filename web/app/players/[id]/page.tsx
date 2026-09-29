import Link from "next/link";
import { notFound } from "next/navigation";
import { PlayerStats } from "@/app/components/PlayerStats";
import { SeasonSelector } from "@/app/components/SeasonSelector";
import {
  ApiError,
  findSimilarPlayers,
  getPlayer,
  getPlayerSeason,
  listPlayerSeasons,
  type Season,
  type SimilarPlayerMatch,
} from "@/lib/api";

export default async function PlayerDetailPage(props: PageProps<"/players/[id]">) {
  const { id } = await props.params;
  const searchParams = await props.searchParams;
  const seasonCompetition =
    typeof searchParams.sc === "string" ? searchParams.sc : undefined;
  const seasonLabel = typeof searchParams.sl === "string" ? searchParams.sl : undefined;
  const selectedSeason: Season | undefined =
    seasonCompetition && seasonLabel
      ? { competition: seasonCompetition, label: seasonLabel }
      : undefined;

  let player;
  try {
    player = selectedSeason
      ? await getPlayerSeason(Number(id), selectedSeason)
      : await getPlayer(Number(id));
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  let seasons: Season[] = [];
  try {
    seasons = await listPlayerSeasons(Number(id));
  } catch {
    seasons = [];
  }

  let similar: SimilarPlayerMatch[] = [];
  try {
    similar = await findSimilarPlayers(Number(id), { season: selectedSeason });
  } catch {
    similar = [];
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{player.name}</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            {player.position} · nacido el {player.date_of_birth}
          </p>
        </div>
        <SeasonSelector
          playerId={Number(id)}
          seasons={seasons}
          selected={selectedSeason}
        />
        <Link
          href={`/compare?a=${player.player_id}`}
          className="w-fit text-sm font-medium underline"
        >
          Comparar con otro jugador
        </Link>
      </section>

      <PlayerStats player={player} />

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold tracking-tight">
          Jugadores más parecidos
          {selectedSeason
            ? ` (${selectedSeason.competition} ${selectedSeason.label})`
            : " (carrera)"}
        </h2>
        {similar.length === 0 && (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            No hay suficientes jugadores ingeridos todavía para comparar.
          </p>
        )}
        {similar.length > 0 && (
          <ul className="divide-y divide-zinc-200 rounded-md border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
            {similar.map((match) => (
              <li key={match.comparison.player2.player_id}>
                <Link
                  href={`/players/${match.comparison.player2.player_id}`}
                  className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-zinc-100 dark:hover:bg-zinc-900"
                >
                  <span>
                    <span className="font-medium">
                      {match.comparison.player2.name}
                    </span>
                    <span className="ml-2 text-xs text-zinc-500 dark:text-zinc-400">
                      {match.candidate_season.competition}{" "}
                      {match.candidate_season.label}
                    </span>
                  </span>
                  <span className="text-sm text-zinc-500 dark:text-zinc-400">
                    {match.comparison.similarity_percentage}% parecido
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
