import type { Player } from "@/lib/api";

const SERIES_A_COLOR = "#2a78d6";
const SERIES_B_COLOR = "#eb6834";

type MetricKey = keyof Pick<
  Player,
  | "goals"
  | "shots"
  | "shots_on_target"
  | "expected_goals"
  | "assists"
  | "key_passes"
  | "passes_completed"
  | "dribbles_completed"
  | "tackles_won"
  | "interceptions"
  | "fouls_committed"
  | "fouls_won"
  | "yellow_cards"
  | "red_cards"
>;

type MetricDef = { label: string; key: MetricKey; format?: (value: number) => string };

const CATEGORIES: { title: string; icon: string; metrics: MetricDef[] }[] = [
  {
    title: "Ataque",
    icon: "⚽",
    metrics: [
      { label: "Goles", key: "goals" },
      { label: "Tiros", key: "shots" },
      { label: "Tiros a puerta", key: "shots_on_target" },
      { label: "xG", key: "expected_goals", format: (v) => v.toFixed(2) },
    ],
  },
  {
    title: "Creación",
    icon: "🎨",
    metrics: [
      { label: "Asistencias", key: "assists" },
      { label: "Pases de gol", key: "key_passes" },
      { label: "Pases completados", key: "passes_completed" },
      { label: "Regates completados", key: "dribbles_completed" },
    ],
  },
  {
    title: "Defensa",
    icon: "🛡️",
    metrics: [
      { label: "Entradas ganadas", key: "tackles_won" },
      { label: "Intercepciones", key: "interceptions" },
    ],
  },
  {
    title: "Disciplina",
    icon: "🟨",
    metrics: [
      { label: "Faltas cometidas", key: "fouls_committed" },
      { label: "Faltas recibidas", key: "fouls_won" },
      { label: "Tarjetas amarillas", key: "yellow_cards" },
      { label: "Tarjetas rojas", key: "red_cards" },
    ],
  },
];

function MetricRow({
  label,
  valueA,
  valueB,
  format,
}: {
  label: string;
  valueA: number;
  valueB: number;
  format: (value: number) => string;
}) {
  const max = Math.max(valueA, valueB, 0.0001);
  const pctA = (valueA / max) * 100;
  const pctB = (valueB / max) * 100;

  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-zinc-500 dark:text-zinc-400">{label}</span>
      <div className="flex items-center gap-2">
        <span
          className="w-12 shrink-0 text-right text-xs font-medium tabular-nums"
          style={{ color: SERIES_A_COLOR }}
        >
          {format(valueA)}
        </span>
        <div className="flex flex-1 flex-col gap-1">
          <div className="h-2 rounded-full bg-zinc-100 dark:bg-zinc-800">
            <div
              className="h-2 rounded-full"
              style={{ width: `${pctA}%`, backgroundColor: SERIES_A_COLOR }}
            />
          </div>
          <div className="h-2 rounded-full bg-zinc-100 dark:bg-zinc-800">
            <div
              className="h-2 rounded-full"
              style={{ width: `${pctB}%`, backgroundColor: SERIES_B_COLOR }}
            />
          </div>
        </div>
        <span
          className="w-12 shrink-0 text-xs font-medium tabular-nums"
          style={{ color: SERIES_B_COLOR }}
        >
          {format(valueB)}
        </span>
      </div>
    </div>
  );
}

export function PlayerCompareChart({
  playerA,
  playerB,
}: {
  playerA: Player;
  playerB: Player;
}) {
  return (
    <div className="flex flex-col gap-6 rounded-md border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex items-center justify-center gap-6 text-sm font-medium">
        <span className="flex items-center gap-2">
          <span
            className="h-3 w-3 rounded-full"
            style={{ backgroundColor: SERIES_A_COLOR }}
          />
          {playerA.name}
        </span>
        <span className="flex items-center gap-2">
          <span
            className="h-3 w-3 rounded-full"
            style={{ backgroundColor: SERIES_B_COLOR }}
          />
          {playerB.name}
        </span>
      </div>
      {CATEGORIES.map((category) => (
        <div key={category.title} className="flex flex-col gap-3">
          <h3 className="flex items-center gap-2 text-sm font-medium text-zinc-500 dark:text-zinc-400">
            <span aria-hidden="true">{category.icon}</span>
            {category.title}
          </h3>
          <div className="flex flex-col gap-3">
            {category.metrics.map((metric) => (
              <MetricRow
                key={metric.label}
                label={metric.label}
                valueA={Number(playerA[metric.key])}
                valueB={Number(playerB[metric.key])}
                format={metric.format ?? ((value) => String(value))}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
