"use client";

import { motion } from "motion/react";
import { useState } from "react";
import type { Player } from "@/lib/api";
import {
  GROUPS,
  METRICS,
  formatMetric,
  metricValue,
  type MetricKey,
} from "@/lib/metrics";

const COLOR_A = "#3d8bff";
const COLOR_B = "#ff6b3d";

/** Metrics a source may not track this season: hide them when both are 0. */
const OPTIONAL: MetricKey[] = [
  "expected_goals",
  "expected_assists",
  "xg_chain",
  "xg_buildup",
  "passes_completed",
  "dribbles_completed",
];

export function comparableMetrics(a: Player, b: Player): MetricKey[] {
  return GROUPS.flatMap((group) => group.metrics).filter(
    (key) => !(OPTIONAL.includes(key) && a[key] === 0 && b[key] === 0),
  );
}

/** +1 when A is better, -1 when B is better, 0 on a tie. */
export function winner(a: number, b: number, key: MetricKey): number {
  if (a === b) return 0;
  const aBetter = METRICS[key].lowerIsBetter ? a < b : a > b;
  return aBetter ? 1 : -1;
}

function Row({
  metric,
  a,
  b,
  perNinety,
  index,
}: {
  metric: MetricKey;
  a: number;
  b: number;
  perNinety: boolean;
  index: number;
}) {
  const max = Math.max(a, b) || 1;
  const result = winner(a, b, metric);
  const info = METRICS[metric];

  return (
    <li className="grid grid-cols-[1fr_auto_1fr] items-center gap-3" title={info.help}>
      <div className="flex items-center justify-end gap-3">
        <span
          className={`font-display text-lg font-bold tabular-nums transition ${result === 1 ? "text-white" : "text-muted"}`}
        >
          {formatMetric(metric, a, perNinety)}
        </span>
        <div className="flex h-3 w-full max-w-[260px] justify-end overflow-hidden rounded-full bg-white/5">
          <motion.div
            className="h-full rounded-full"
            style={{
              background: `linear-gradient(270deg, ${COLOR_A}, ${COLOR_A}55)`,
              boxShadow: result === 1 ? `0 0 14px ${COLOR_A}` : "none",
              opacity: result === -1 ? 0.45 : 1,
            }}
            initial={{ width: 0 }}
            whileInView={{ width: `${(a / max) * 100}%` }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: index * 0.03, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>
      </div>
      <span className="w-24 text-center text-xs font-medium text-ink/80 sm:w-32">
        {info.short}
      </span>
      <div className="flex items-center gap-3">
        <div className="flex h-3 w-full max-w-[260px] overflow-hidden rounded-full bg-white/5">
          <motion.div
            className="h-full rounded-full"
            style={{
              background: `linear-gradient(90deg, ${COLOR_B}, ${COLOR_B}55)`,
              boxShadow: result === -1 ? `0 0 14px ${COLOR_B}` : "none",
              opacity: result === 1 ? 0.45 : 1,
            }}
            initial={{ width: 0 }}
            whileInView={{ width: `${(b / max) * 100}%` }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: index * 0.03, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>
        <span
          className={`font-display text-lg font-bold tabular-nums transition ${result === -1 ? "text-white" : "text-muted"}`}
        >
          {formatMetric(metric, b, perNinety)}
        </span>
      </div>
    </li>
  );
}

export function HeadToHead({ playerA, playerB }: { playerA: Player; playerB: Player }) {
  const bothHaveMinutes = playerA.minutes_played > 0 && playerB.minutes_played > 0;
  const [perNinety, setPerNinety] = useState(bothHaveMinutes);
  const shown = comparableMetrics(playerA, playerB);
  let rowIndex = 0;

  return (
    <section className="glass flex flex-col gap-6 rounded-3xl p-5 sm:p-7">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl font-bold tracking-tight">Métrica a métrica</h2>
          <p className="text-sm text-muted">
            {perNinety
              ? "Por cada 90 minutos: justo aunque uno haya jugado más que el otro."
              : "Totales de la temporada elegida."}{" "}
            Pasa el ratón por una métrica para ver qué significa.
          </p>
        </div>
        {bothHaveMinutes && (
          <div className="glass flex rounded-full p-1 text-xs font-semibold">
            {[
              { value: true, label: "Por 90'" },
              { value: false, label: "Totales" },
            ].map((option) => (
              <button
                key={option.label}
                type="button"
                onClick={() => setPerNinety(option.value)}
                className={`rounded-full px-3 py-1.5 transition ${perNinety === option.value ? "bg-white text-black" : "text-muted hover:text-ink"}`}
              >
                {option.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {GROUPS.map((group) => {
        const metrics = group.metrics.filter((key) => shown.includes(key));
        if (metrics.length === 0) return null;
        return (
          <div key={group.key} className="flex flex-col gap-3">
            <h3 className="text-center text-[11px] font-semibold uppercase tracking-[0.25em] text-muted">
              {group.title}
            </h3>
            <ul className="flex flex-col gap-3">
              {metrics.map((metric) => (
                <Row
                  key={`${metric}-${perNinety}`}
                  metric={metric}
                  a={metricValue(playerA, metric, perNinety)}
                  b={metricValue(playerB, metric, perNinety)}
                  perNinety={perNinety}
                  index={rowIndex++}
                />
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}
