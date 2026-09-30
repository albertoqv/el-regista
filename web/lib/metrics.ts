import type { LeaderMetric, Player } from "@/lib/api";

export type MetricKey = keyof Pick<
  Player,
  | "goals"
  | "assists"
  | "shots"
  | "shots_on_target"
  | "expected_goals"
  | "expected_assists"
  | "passes_completed"
  | "key_passes"
  | "dribbles_completed"
  | "tackles_won"
  | "interceptions"
  | "fouls_committed"
  | "fouls_won"
  | "yellow_cards"
  | "red_cards"
  | "xg_chain"
  | "xg_buildup"
  | "minutes_played"
>;

export type MetricGroup = "attack" | "creation" | "defense" | "discipline";

export type MetricInfo = {
  key: MetricKey;
  label: string;
  short: string;
  help: string;
  group: MetricGroup;
  decimals?: number;
  /** For fouls or cards, fewer is better. */
  lowerIsBetter?: boolean;
};

export const METRICS: Record<MetricKey, MetricInfo> = {
  goals: { key: "goals", label: "Goles", short: "Goles", group: "attack", help: "Goles marcados." },
  expected_goals: {
    key: "expected_goals",
    label: "Goles esperados (xG)",
    short: "xG",
    group: "attack",
    decimals: 2,
    help: "Goles que marcaría un jugador medio con esas mismas ocasiones. Si marca más que su xG, está definiendo por encima de lo normal.",
  },
  shots: { key: "shots", label: "Tiros", short: "Tiros", group: "attack", help: "Disparos totales." },
  shots_on_target: {
    key: "shots_on_target",
    label: "Tiros a puerta",
    short: "A puerta",
    group: "attack",
    help: "Disparos entre los tres palos.",
  },
  assists: { key: "assists", label: "Asistencias", short: "Asist.", group: "creation", help: "Pases que acaban en gol." },
  expected_assists: {
    key: "expected_assists",
    label: "Asistencias esperadas (xA)",
    short: "xA",
    group: "creation",
    decimals: 2,
    help: "Calidad de las ocasiones que crea con sus pases, aunque el compañero no marque.",
  },
  key_passes: {
    key: "key_passes",
    label: "Pases clave",
    short: "P. clave",
    group: "creation",
    help: "Pases que terminan en un tiro de un compañero.",
  },
  xg_chain: {
    key: "xg_chain",
    label: "Participación en jugadas de peligro (xGChain)",
    short: "xGChain",
    group: "creation",
    decimals: 2,
    help: "xG total de las jugadas en las que interviene, sea como sea. Mide cuánto pesa en el ataque del equipo.",
  },
  xg_buildup: {
    key: "xg_buildup",
    label: "Construcción de juego (xGBuildup)",
    short: "Buildup",
    group: "creation",
    decimals: 2,
    help: "Como xGChain pero sin contar el tiro ni el último pase: premia a quien prepara la jugada.",
  },
  passes_completed: {
    key: "passes_completed",
    label: "Pases completados",
    short: "Pases",
    group: "creation",
    help: "Pases que llegan a un compañero.",
  },
  dribbles_completed: {
    key: "dribbles_completed",
    label: "Regates completados",
    short: "Regates",
    group: "creation",
    help: "Regates en los que supera al rival.",
  },
  tackles_won: {
    key: "tackles_won",
    label: "Entradas ganadas",
    short: "Entradas",
    group: "defense",
    help: "Entradas con las que su equipo recupera el balón.",
  },
  interceptions: {
    key: "interceptions",
    label: "Intercepciones",
    short: "Intercep.",
    group: "defense",
    help: "Pases rivales que corta.",
  },
  fouls_won: {
    key: "fouls_won",
    label: "Faltas recibidas",
    short: "F. recibidas",
    group: "discipline",
    help: "Faltas que le hacen: suele indicar desborde.",
  },
  fouls_committed: {
    key: "fouls_committed",
    label: "Faltas cometidas",
    short: "F. cometidas",
    group: "discipline",
    lowerIsBetter: true,
    help: "Faltas que comete.",
  },
  yellow_cards: {
    key: "yellow_cards",
    label: "Tarjetas amarillas",
    short: "Amarillas",
    group: "discipline",
    lowerIsBetter: true,
    help: "Amonestaciones.",
  },
  red_cards: {
    key: "red_cards",
    label: "Tarjetas rojas",
    short: "Rojas",
    group: "discipline",
    lowerIsBetter: true,
    help: "Expulsiones.",
  },
  minutes_played: {
    key: "minutes_played",
    label: "Minutos jugados",
    short: "Minutos",
    group: "discipline",
    help: "Minutos en el campo.",
  },
};

export const GROUPS: { key: MetricGroup; title: string; metrics: MetricKey[] }[] = [
  {
    key: "attack",
    title: "Ataque",
    metrics: ["goals", "expected_goals", "shots", "shots_on_target"],
  },
  {
    key: "creation",
    title: "Creación",
    metrics: [
      "assists",
      "expected_assists",
      "key_passes",
      "xg_chain",
      "xg_buildup",
      "passes_completed",
      "dribbles_completed",
    ],
  },
  { key: "defense", title: "Defensa", metrics: ["tackles_won", "interceptions"] },
  {
    key: "discipline",
    title: "Disciplina",
    metrics: ["fouls_won", "fouls_committed", "yellow_cards", "red_cards"],
  },
];

/** Radar axes, in drawing order (attack → creation → defense). */
export const RADAR_METRICS: MetricKey[] = [
  "goals",
  "expected_goals",
  "shots",
  "shots_on_target",
  "assists",
  "expected_assists",
  "key_passes",
  "xg_chain",
  "xg_buildup",
  "passes_completed",
  "dribbles_completed",
  "tackles_won",
  "interceptions",
  "fouls_won",
];

export const LEADER_TABS: { metric: LeaderMetric; label: string }[] = [
  { metric: "goals", label: "Goles" },
  { metric: "assists", label: "Asistencias" },
  { metric: "expected_goals", label: "xG" },
  { metric: "expected_assists", label: "xA" },
  { metric: "key_passes", label: "Pases clave" },
  { metric: "xg_chain", label: "xGChain" },
  { metric: "shots", label: "Tiros" },
  { metric: "tackles_won", label: "Entradas" },
  { metric: "interceptions", label: "Intercepciones" },
];

export function metricValue(player: Player, key: MetricKey, perNinety: boolean): number {
  const raw = player[key];
  if (!perNinety || key === "minutes_played") return raw;
  return player.minutes_played > 0 ? (raw * 90) / player.minutes_played : 0;
}

export function formatMetric(key: MetricKey, value: number, perNinety = false): string {
  const decimals = perNinety ? 2 : (METRICS[key].decimals ?? 0);
  return value.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** Wyscout-style colour scale for percentiles. */
export function percentileColor(percentile: number): string {
  if (percentile >= 90) return "#22d3a5";
  if (percentile >= 70) return "#4ade80";
  if (percentile >= 50) return "#facc15";
  if (percentile >= 30) return "#fb923c";
  return "#f87171";
}
