"use client";

import { motion } from "motion/react";
import { comparableMetrics, winner } from "@/app/components/HeadToHead";
import type { Player } from "@/lib/api";
import { METRICS, metricValue, type MetricKey } from "@/lib/metrics";

/** Tug-of-war summary: how many metrics each player wins (per 90 when possible). */
export function CompareVerdict({
  playerA,
  playerB,
  only,
}: {
  playerA: Player;
  playerB: Player;
  only?: MetricKey[];
}) {
  const perNinety = playerA.minutes_played > 0 && playerB.minutes_played > 0;
  const metrics = comparableMetrics(playerA, playerB, only).filter((key) => key !== "minutes_played");
  const winsA: MetricKey[] = [];
  const winsB: MetricKey[] = [];
  for (const key of metrics) {
    const result = winner(
      metricValue(playerA, key, perNinety),
      metricValue(playerB, key, perNinety),
      key,
    );
    if (result === 1) winsA.push(key);
    if (result === -1) winsB.push(key);
  }
  const decided = winsA.length + winsB.length || 1;
  const shareA = (winsA.length / decided) * 100;
  const leader =
    winsA.length === winsB.length ? null : winsA.length > winsB.length ? playerA : playerB;

  // Where the gap is widest, relative to the better value.
  const margin = (key: MetricKey) => {
    const a = metricValue(playerA, key, perNinety);
    const b = metricValue(playerB, key, perNinety);
    return Math.abs(a - b) / (Math.max(a, b) || 1);
  };
  const highlights = (wins: MetricKey[]) =>
    [...wins]
      .sort((x, y) => margin(y) - margin(x))
      .slice(0, 3)
      .map((key) => METRICS[key].short)
      .join(", ");

  return (
    <section className="glass flex flex-col gap-5 rounded-lg p-6">
      <div className="text-center">
        <p className="text-xs font-semibold text-muted">Veredicto</p>
        <h2 className="font-heading text-2xl tracking-tight sm:text-3xl">
          {leader ? (
            <>
              <span style={{ color: leader === playerA ? "#2350d8" : "#c93c17" }}>{leader.name}</span>{" "}
              gana en {Math.max(winsA.length, winsB.length)} de {metrics.length} métricas
            </>
          ) : (
            <>Empate técnico: {winsA.length} métricas cada uno</>
          )}
        </h2>
        <p className="mt-1 text-sm text-muted">
          {perNinety ? "Comparado por cada 90 minutos jugados." : "Comparado en totales."}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <span className="font-display text-3xl font-bold text-side-a tabular-nums">{winsA.length}</span>
        <div className="relative h-4 flex-1 overflow-hidden rounded-full bg-side-b/80">
          <motion.div
            className="absolute inset-y-0 left-0 rounded-full bg-side-a"
            initial={{ width: "50%" }}
            whileInView={{ width: `${shareA}%` }}
            viewport={{ once: true }}
            transition={{ type: "spring", stiffness: 60, damping: 12, delay: 0.3 }}
          />
          <div className="absolute inset-y-0 left-1/2 w-px bg-ink/60" />
        </div>
        <span className="font-display text-3xl font-bold text-side-b tabular-nums">{winsB.length}</span>
      </div>

      <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        {winsA.length > 0 && (
          <p className="rounded-lg bg-side-a/10 p-3 text-ink/90">
            <strong className="text-side-a">{playerA.name}</strong> destaca en {highlights(winsA)}.
          </p>
        )}
        {winsB.length > 0 && (
          <p className="rounded-lg bg-side-b/10 p-3 text-ink/90">
            <strong className="text-side-b">{playerB.name}</strong> destaca en {highlights(winsB)}.
          </p>
        )}
      </div>
    </section>
  );
}
