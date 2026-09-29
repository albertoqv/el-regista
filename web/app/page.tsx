import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { IconTarget, IconTrophy } from "@/app/components/icons";
import { Leaderboard } from "@/app/components/Leaderboard";
import { PlayerSearchForm } from "@/app/components/PlayerSearchForm";
import { listPlayers, type Player } from "@/lib/api";

const LEADERBOARD_SIZE = 8;
const RECENT_LIST_SIZE = 50;

async function loadHome(): Promise<{
  recent: Player[];
  topScorers: Player[];
  topAssisters: Player[];
  error: string | null;
}> {
  try {
    const [recent, topScorers, topAssisters] = await Promise.all([
      listPlayers({ sort: "recent", limit: RECENT_LIST_SIZE }),
      listPlayers({ sort: "goals", limit: LEADERBOARD_SIZE }),
      listPlayers({ sort: "assists", limit: LEADERBOARD_SIZE }),
    ]);
    return { recent, topScorers, topAssisters, error: null };
  } catch {
    return {
      recent: [],
      topScorers: [],
      topAssisters: [],
      error:
        "No se ha podido conectar con la API. Comprueba que esté arrancada en NEXT_PUBLIC_API_URL.",
    };
  }
}

export default async function HomePage() {
  const { recent, topScorers, topAssisters, error } = await loadHome();

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Jugadores</h1>
        <PlayerSearchForm />
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Las 5 grandes ligas europeas, actualizadas cada semana.
        </p>
      </section>

      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {!error && recent.length === 0 && (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Todavía no hay jugadores disponibles. Vuelve pronto.
        </p>
      )}

      {recent.length > 0 && (
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2">
          <Leaderboard
            title="Top goleadores"
            icon={IconTrophy}
            players={topScorers}
            metricKey="goals"
          />
          <Leaderboard
            title="Top asistentes"
            icon={IconTarget}
            players={topAssisters}
            metricKey="assists"
          />
        </div>
      )}

      {recent.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold tracking-tight">
            Destacados de la temporada más reciente
          </h2>
          <ul className="divide-y divide-zinc-200 rounded-md border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
            {recent.map((player) => (
              <li key={player.player_id}>
                <Link
                  href={`/players/${player.player_id}`}
                  className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-zinc-100 dark:hover:bg-zinc-900"
                >
                  <span className="flex items-center gap-3">
                    <Avatar
                      name={player.name}
                      photoUrl={player.photo_url}
                      size={40}
                    />
                    <span className="font-medium">{player.name}</span>
                  </span>
                  <span className="text-sm text-zinc-500 dark:text-zinc-400">
                    {player.position} · {player.goals}G {player.assists}A
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
