import type { PlayerShot, ShotMetric } from "@/lib/api";

// Same geometry as the backend (domain/shots.py): 105 x 68 m pitch.
const PITCH_LENGTH = 105;
const PITCH_WIDTH = 68;
export const LATE_MINUTE = 75;
const SET_PIECES = new Set(["FromCorner", "SetPiece", "DirectFreekick"]);

export function isOutsideBox(x: number, y: number): boolean {
  return (1 - x) * PITCH_LENGTH > 16.5 || Math.abs(y - 0.5) * PITCH_WIDTH > 20.16;
}

export const BUCKETS = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'+"];

function bucketOf(minute: number): number {
  return Math.min(5, Math.max(0, Math.ceil(minute / 15) - 1));
}

export type ShotSummary = {
  shots: number;
  goals: number;
  xg: number;
  npGoals: number;
  npXg: number;
  npShots: number;
  lateGoals: number;
  decisiveGoals: number;
  headedGoals: number;
  outsideBoxGoals: number;
  setPieceGoals: number;
  goalsByBucket: number[];
  xgByBucket: number[];
  body: Record<"LeftFoot" | "RightFoot" | "Head" | "OtherBodyPart", { shots: number; goals: number }>;
};

export function summarize(shots: PlayerShot[]): ShotSummary {
  const summary: ShotSummary = {
    shots: shots.length,
    goals: 0,
    xg: 0,
    npGoals: 0,
    npXg: 0,
    npShots: 0,
    lateGoals: 0,
    decisiveGoals: 0,
    headedGoals: 0,
    outsideBoxGoals: 0,
    setPieceGoals: 0,
    goalsByBucket: [0, 0, 0, 0, 0, 0],
    xgByBucket: [0, 0, 0, 0, 0, 0],
    body: {
      LeftFoot: { shots: 0, goals: 0 },
      RightFoot: { shots: 0, goals: 0 },
      Head: { shots: 0, goals: 0 },
      OtherBodyPart: { shots: 0, goals: 0 },
    },
  };
  for (const shot of shots) {
    const goal = shot.result === "Goal";
    const penalty = shot.situation === "Penalty";
    summary.xg += shot.xg;
    summary.xgByBucket[bucketOf(shot.minute)] += shot.xg;
    const part = summary.body[shot.shot_type as keyof ShotSummary["body"]] ?? summary.body.OtherBodyPart;
    part.shots += 1;
    if (!penalty) {
      summary.npShots += 1;
      summary.npXg += shot.xg;
    }
    if (!goal) continue;
    part.goals += 1;
    summary.goals += 1;
    summary.goalsByBucket[bucketOf(shot.minute)] += 1;
    if (!penalty) summary.npGoals += 1;
    if (shot.minute >= LATE_MINUTE) summary.lateGoals += 1;
    if (shot.decisive) summary.decisiveGoals += 1;
    if (shot.shot_type === "Head") summary.headedGoals += 1;
    if (isOutsideBox(shot.x, shot.y)) summary.outsideBoxGoals += 1;
    if (SET_PIECES.has(shot.situation)) summary.setPieceGoals += 1;
  }
  return summary;
}

export type ShotMetricInfo = {
  metric: ShotMetric;
  label: string;
  title: string;
  help: string;
  decimals: number;
  unit: string;
};

export const SHOT_METRICS: ShotMetricInfo[] = [
  {
    metric: "late_goals",
    label: "Tramo final",
    title: "Los que aparecen al final",
    help: "Goles a partir del minuto 75. Los que no se cansan.",
    decimals: 0,
    unit: "goles",
  },
  {
    metric: "decisive_goals",
    label: "Goles decisivos",
    title: "Goles que valen puntos",
    help: "Goles que empatan el partido o ponen a su equipo por delante. Nada de hacer el 4-0.",
    decimals: 0,
    unit: "goles",
  },
  {
    metric: "late_decisive_goals",
    label: "Decisivos al final",
    title: "Sangre fría en el 75'+",
    help: "Goles decisivos a partir del minuto 75: los que salvan partidos.",
    decimals: 0,
    unit: "goles",
  },
  {
    metric: "finishing",
    label: "Definición",
    title: "Los que la meten más de lo esperado",
    help: "Goles sin penaltis menos goles esperados (xG). Positivo = define mejor que un jugador medio con esas ocasiones.",
    decimals: 2,
    unit: "goles sobre lo esperado",
  },
  {
    metric: "npxg_per_shot",
    label: "Calidad de tiro",
    title: "Los que eligen bien cuándo tirar",
    help: "xG medio por disparo (sin penaltis, mínimo 10 tiros). Alto = tira desde buenas posiciones.",
    decimals: 2,
    unit: "xG por tiro",
  },
  {
    metric: "outside_box_goals",
    label: "Desde lejos",
    title: "Golazos desde fuera del área",
    help: "Goles marcados desde fuera del área grande.",
    decimals: 0,
    unit: "goles",
  },
  {
    metric: "headed_goals",
    label: "De cabeza",
    title: "Los reyes del juego aéreo",
    help: "Goles de cabeza.",
    decimals: 0,
    unit: "goles",
  },
  {
    metric: "set_piece_goals",
    label: "Balón parado",
    title: "Especialistas a balón parado",
    help: "Goles tras córner, falta directa u otras jugadas de estrategia (sin penaltis).",
    decimals: 0,
    unit: "goles",
  },
];
