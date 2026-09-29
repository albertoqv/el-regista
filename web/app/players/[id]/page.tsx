import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, findSimilarPlayers, getPlayer, type Comparison } from "@/lib/api";

export default async function PlayerDetailPage(
  props: PageProps<"/players/[id]">,
) {
  const { id } = await props.params;

  let player;
  try {
    player = await getPlayer(Number(id));
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  let similar: Comparison[] = [];
  try {
    similar = await findSimilarPlayers(Number(id));
  } catch {
    similar = [];
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">{player.name}</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {player.position} · nacido el {player.date_of_birth}
        </p>
        <p className="mt-2 text-lg">
          {player.goals} goles · {player.assists} asistencias
        </p>
        <Link
          href={`/compare?a=${player.player_id}`}
          className="mt-2 w-fit text-sm font-medium underline"
        >
          Comparar con otro jugador
        </Link>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold tracking-tight">
          Jugadores más parecidos
        </h2>
        {similar.length === 0 && (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            No hay suficientes jugadores ingeridos todavía para comparar.
          </p>
        )}
        {similar.length > 0 && (
          <ul className="divide-y divide-zinc-200 rounded-md border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
            {similar.map((comparison) => (
              <li key={comparison.player2.player_id}>
                <Link
                  href={`/players/${comparison.player2.player_id}`}
                  className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-zinc-100 dark:hover:bg-zinc-900"
                >
                  <span className="font-medium">{comparison.player2.name}</span>
                  <span className="text-sm text-zinc-500 dark:text-zinc-400">
                    {comparison.similarity_percentage}% parecido
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
