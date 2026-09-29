import Link from "next/link";
import { CompareForm } from "@/app/components/CompareForm";
import { ApiError, comparePlayers } from "@/lib/api";

export default async function ComparePage(props: PageProps<"/compare">) {
  const searchParams = await props.searchParams;
  const rawA = searchParams.a;
  const rawB = searchParams.b;
  const idA = Array.isArray(rawA) ? rawA[0] : rawA;
  const idB = Array.isArray(rawB) ? rawB[0] : rawB;

  let result = null;
  let error: string | null = null;

  if (idA && idB) {
    try {
      result = await comparePlayers(Number(idA), Number(idB));
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

      {result && (
        <section className="rounded-md border border-zinc-200 p-6 dark:border-zinc-800">
          <div className="flex items-center justify-between gap-6">
            <Link
              href={`/players/${result.player1.player_id}`}
              className="text-lg font-medium hover:underline"
            >
              {result.player1.name}
            </Link>
            <span className="text-2xl font-semibold tabular-nums">
              {result.similarity_percentage}%
            </span>
            <Link
              href={`/players/${result.player2.player_id}`}
              className="text-lg font-medium hover:underline"
            >
              {result.player2.name}
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
