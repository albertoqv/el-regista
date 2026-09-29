import type { Player } from "@/lib/api";

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-1 rounded-md border border-zinc-200 px-4 py-3 dark:border-zinc-800">
      <span className="text-xs text-zinc-500 dark:text-zinc-400">{label}</span>
      <span className="text-xl font-semibold">{value}</span>
    </div>
  );
}

function StatGroup({
  title,
  tiles,
}: {
  title: string;
  tiles: { label: string; value: string | number }[];
}) {
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
        {title}
      </h3>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {tiles.map((tile) => (
          <StatTile key={tile.label} label={tile.label} value={tile.value} />
        ))}
      </div>
    </div>
  );
}

export function PlayerStats({ player }: { player: Player }) {
  return (
    <div className="flex flex-col gap-6">
      <StatGroup
        title="Ataque"
        tiles={[
          { label: "Goles", value: player.goals },
          { label: "Tiros", value: player.shots },
          { label: "Tiros a puerta", value: player.shots_on_target },
          { label: "xG", value: player.expected_goals.toFixed(2) },
        ]}
      />
      <StatGroup
        title="Creación"
        tiles={[
          { label: "Asistencias", value: player.assists },
          { label: "Pases de gol", value: player.key_passes },
          {
            label: "Pases completados",
            value: `${player.passes_completed}/${player.passes_attempted}`,
          },
          {
            label: "Regates completados",
            value: `${player.dribbles_completed}/${player.dribbles_attempted}`,
          },
        ]}
      />
      <StatGroup
        title="Defensa"
        tiles={[
          { label: "Entradas ganadas", value: player.tackles_won },
          { label: "Intercepciones", value: player.interceptions },
        ]}
      />
      <StatGroup
        title="Disciplina"
        tiles={[
          { label: "Faltas cometidas", value: player.fouls_committed },
          { label: "Faltas recibidas", value: player.fouls_won },
          { label: "Tarjetas amarillas", value: player.yellow_cards },
          { label: "Tarjetas rojas", value: player.red_cards },
        ]}
      />
    </div>
  );
}
