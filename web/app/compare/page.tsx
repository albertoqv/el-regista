import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { CompareForm } from "@/app/components/CompareForm";
import { PlayerCompareChart } from "@/app/components/PlayerCompareChart";
import { SimilarityMeter } from "@/app/components/SimilarityMeter";
import { ApiError, comparePlayers, getPlayer, type Comparison, type Player } from "@/lib/api";

export default async function ComparePage(props: PageProps<"/compare">) {
  const searchParams = await props.searchParams;
  const rawA = searchParams.a;
  const rawB = searchParams.b;
  const idA = Array.isArray(rawA) ? rawA[0] : rawA;
  const idB = Array.isArray(rawB) ? rawB[0] : rawB;

  let result: Comparison | null = null;
  let playerA: Player | null = null;
  let playerB: Player | null = null;
  let error: string | null = null;

  if (idA && idB) {
    try {
      [result, playerA, playerB] = await Promise.all([
        comparePlayers(Number(idA), Number(idB)),
        getPlayer(Number(idA)),
        getPlayer(Number(idB)),
      ]);
    } catch (thrown) {
      error =
        thrown instanceof ApiError && thrown.status === 404
          ? "Alguno de los dos jugadores no existe."
          : "No se ha podido comparar a los jugadores.";
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">
          Comparar jugadores
        </h1>
        <CompareForm defaultA={idA ?? ""} defaultB={idB ?? ""} />
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
            </Link>
            <SimilarityMeter percentage={result.similarity_percentage} />
            <Link
              href={`/players/${playerB.player_id}`}
              className="flex flex-col items-center gap-2 text-center hover:underline"
            >
              <Avatar name={playerB.name} photoUrl={playerB.photo_url} size={64} />
              <span className="text-lg font-medium">{playerB.name}</span>
            </Link>
          </section>

          <PlayerCompareChart playerA={playerA} playerB={playerB} />
        </>
      )}
    </div>
  );
}
