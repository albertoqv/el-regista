import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { Leaderboard } from "@/app/components/Leaderboard";
import { PlayerSearchForm } from "@/app/components/PlayerSearchForm";
import { listPlayers, sortByRecency, type Player } from "@/lib/api";

async function loadPlayers(): Promise<{ players: Player[]; error: string | null }> {
  try {
    const players = await listPlayers();
    return { players: sortByRecency(players), error: null };
  } catch {
    return {
      players: [],
      error:
        "No se ha podido conectar con la API. Comprueba que esté arrancada en NEXT_PUBLIC_API_URL.",
    };
  }
}

export default async function HomePage() {
  const { players, error } = await loadPlayers();

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">Jugadores</h1>
        <PlayerSearchForm players={players} />
        {players.length > 0 && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            {players.length} jugador{players.length === 1 ? "" : "es"} disponible
            {players.length === 1 ? "" : "s"}.
          </p>
        )}
      </section>

      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {!error && players.length === 0 && (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Todavía no hay jugadores disponibles. Vuelve pronto.
        </p>
      )}

      {players.length > 0 && (
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2">
          <Leaderboard
            title="Top goleadores"
            icon="🥇"
            players={players}
            metricKey="goals"
          />
          <Leaderboard
            title="Top asistentes"
            icon="🎯"
            players={players}
            metricKey="assists"
          />
        </div>
      )}

      {players.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold tracking-tight">
            Todos los jugadores
          </h2>
          <ul className="divide-y divide-zinc-200 rounded-md border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
            {players.map((player) => (
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
