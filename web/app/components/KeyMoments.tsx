"use client";

import { motion } from "motion/react";
import type { PlayerShot } from "@/lib/api";
import { summarize, type ShotSummary } from "@/lib/shots";

const ROWS: { label: string; help: string; value: (s: ShotSummary) => number; decimals?: number }[] = [
  { label: "Goles en el tramo final (75'+)", help: "Los que aparecen cuando más pesa.", value: (s) => s.lateGoals },
  { label: "Goles decisivos", help: "Goles que empatan o ponen por delante.", value: (s) => s.decisiveGoals },
  {
    label: "Goles vs lo esperado",
    help: "Goles sin penaltis menos xG: define mejor (+) o peor (−) que la media.",
    value: (s) => s.npGoals - s.npXg,
    decimals: 1,
  },
  {
    label: "xG por tiro",
    help: "Calidad media de sus ocasiones (sin penaltis).",
    value: (s) => (s.npShots ? s.npXg / s.npShots : 0),
    decimals: 2,
  },
  { label: "Goles desde fuera del área", help: "Disparos lejanos convertidos.", value: (s) => s.outsideBoxGoals },
  { label: "Goles de cabeza", help: "Juego aéreo.", value: (s) => s.headedGoals },
  { label: "Goles a balón parado", help: "Córners, faltas y jugadas de estrategia.", value: (s) => s.setPieceGoals },
];

function show(value: number, decimals = 0): string {
  const text = value.toLocaleString("es-ES", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  return decimals === 1 && value > 0 ? `+${text}` : text;
}

/** Face-off of the two shot profiles: the moments that decide matches. */
export function KeyMoments({
  nameA,
  nameB,
  shotsA,
  shotsB,
}: {
  nameA: string;
  nameB: string;
  shotsA: PlayerShot[];
  shotsB: PlayerShot[];
}) {
  if (shotsA.length === 0 || shotsB.length === 0) return null;
  const a = summarize(shotsA);
  const b = summarize(shotsB);

  return (
    <section className="glass flex flex-col gap-5 rounded-3xl p-5 sm:p-7">
      <div>
        <h2 className="font-display text-2xl font-bold tracking-tight">Momentos clave</h2>
        <p className="text-sm text-muted">
          Sacado de sus {a.shots} y {b.shots} tiros: cuándo, cómo y si sirvieron para ganar.
        </p>
      </div>
      <ul className="flex flex-col gap-3">
        {ROWS.map((row, index) => {
          const valueA = row.value(a);
          const valueB = row.value(b);
          const span = Math.max(Math.abs(valueA), Math.abs(valueB)) || 1;
          const winner = valueA === valueB ? 0 : valueA > valueB ? 1 : -1;
          return (
            <li key={row.label} className="grid grid-cols-[64px_1fr_64px] items-center gap-3" title={row.help}>
              <span className={`text-right font-display text-xl font-bold tabular-nums ${winner === 1 ? "text-side-a" : "text-muted"}`}>
                {show(valueA, row.decimals)}
              </span>
              <div className="flex flex-col gap-1">
                <span className="text-center text-xs font-medium text-ink/80">{row.label}</span>
                <div className="flex h-2 gap-1">
                  <div className="flex flex-1 justify-end overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      className="h-full rounded-full bg-side-a"
                      style={{ opacity: winner === -1 ? 0.4 : 1 }}
                      initial={{ width: 0 }}
                      whileInView={{ width: `${(Math.max(valueA, 0) / span) * 100}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.8, delay: index * 0.05 }}
                    />
                  </div>
                  <div className="flex-1 overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      className="h-full rounded-full bg-side-b"
                      style={{ opacity: winner === 1 ? 0.4 : 1 }}
                      initial={{ width: 0 }}
                      whileInView={{ width: `${(Math.max(valueB, 0) / span) * 100}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.8, delay: index * 0.05 }}
                    />
                  </div>
                </div>
              </div>
              <span className={`font-display text-xl font-bold tabular-nums ${winner === -1 ? "text-side-b" : "text-muted"}`}>
                {show(valueB, row.decimals)}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="text-center text-xs text-muted">
        <span className="text-side-a">{nameA}</span> · <span className="text-side-b">{nameB}</span>
      </p>
    </section>
  );
}
