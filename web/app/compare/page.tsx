import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { ComparePicker } from "@/app/components/ComparePicker";
import { PlayerCompareChart } from "@/app/components/PlayerCompareChart";
import { SimilarityMeter } from "@/app/components/SimilarityMeter";
import {
  ApiError,
  comparePlayers,
  getPlayer,
  getPlayerSeason,
  listPlayers,
  type Comparison,
  type Player,
  type Season,
} from "@/lib/api";

function paramValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function seasonFromParams(
  competition: string | undefined,
  label: string | undefined,
): Season | null {
  return competition && label ? { competition, label } : null;
}

export default async function ComparePage(props: PageProps<"/compare">) {
  const searchParams = await props.searchParams;
  const rawA = paramValue(searchParams.a);
  const rawB = paramValue(searchParams.b);
  const idA = rawA ? Number(rawA) : null;
  const idB = rawB ? Number(rawB) : null;
  const seasonA = seasonFromParams(
    paramValue(searchParams.sac),
    paramValue(searchParams.sal),
  );
  const seasonB = seasonFromParams(
    paramValue(searchParams.sbc),
    paramValue(searchParams.sbl),
  );

  let players: Player[] = [];
  try {
    players = await listPlayers();
  } catch {
    players = [];
  }

  let result: Comparison | null = null;
  let playerA: Player | null = null;
  let playerB: Player | null = null;
  let error: string | null = null;

  if (idA && idB) {
    try {
      [result, playerA, playerB] = await Promise.all([
        comparePlayers(idA, idB, { seasonA: seasonA ?? undefined, seasonB: seasonB ?? undefined }),
        seasonA ? getPlayerSeason(idA, seasonA) : getPlayer(idA),
        seasonB ? getPlayerSeason(idB, seasonB) : getPlayer(idB),
      ]);
    } catch (thrown) {
      error =
        thrown instanceof ApiError && thrown.status === 404
          ? "Alguno de los dos jugadores no existe para la temporada elegida."
          : "No se ha podido comparar a los jugadores.";
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">
          Comparar jugadores
        </h1>
        <ComparePicker
          players={players}
          defaultA={idA}
          defaultB={idB}
          defaultSeasonA={seasonA}
          defaultSeasonB={seasonB}
        />
      </section>

      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {result && playerA && playerB && (
        <>
          <section className="flex items-center justify-center gap-8 rounded-md border border-zinc-200 p-6 dark:border-zinc-800">
            <Link
              href={`/players/${playerA.player_id}`}
              className="flex flex-col items-center gap-2 text-center hover:underline"
            >
              <Avatar name={playerA.name} photoUrl={playerA.photo_url} size={64} />
              <span className="text-lg font-medium">{playerA.name}</span>
              <span className="text-xs text-zinc-500 dark:text-zinc-400">
                {seasonA ? `${seasonA.competition} ${seasonA.label}` : "Carrera"}
              </span>
            </Link>
            <SimilarityMeter percentage={result.similarity_percentage} />
            <Link
              href={`/players/${playerB.player_id}`}
              className="flex flex-col items-center gap-2 text-center hover:underline"
            >
              <Avatar name={playerB.name} photoUrl={playerB.photo_url} size={64} />
              <span className="text-lg font-medium">{playerB.name}</span>
              <span className="text-xs text-zinc-500 dark:text-zinc-400">
                {seasonB ? `${seasonB.competition} ${seasonB.label}` : "Carrera"}
              </span>
            </Link>
          </section>

          <PlayerCompareChart playerA={playerA} playerB={playerB} />
        </>
      )}
    </div>
  );
}
