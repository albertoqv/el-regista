"use client";

import { motion } from "motion/react";
import { ScoutNote } from "@/app/components/ScoutNote";
import { ShotMap } from "@/app/components/ShotMap";
import type { PlayerShot } from "@/lib/api";
import { BUCKETS, summarize } from "@/lib/shots";

const BODY_LABEL = {
  RightFoot: "Pie derecho",
  LeftFoot: "Pie izquierdo",
  Head: "Cabeza",
  OtherBodyPart: "Otras",
} as const;

function MinuteChart({ goals, xg, color }: { goals: number[]; xg: number[]; color: string }) {
  const max = Math.max(...goals, ...xg, 1);
  const best = goals.indexOf(Math.max(...goals));
  return (
    <div className="flex h-44 items-end gap-2">
      {BUCKETS.map((label, index) => (
        <div key={label} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
          <span className="font-display text-sm font-bold tabular-nums">{goals[index]}</span>
          <div className="relative flex h-full w-full items-end justify-center">
            <motion.div
              className="absolute bottom-0 w-full rounded-t-md border border-dashed border-white/25"
              initial={{ height: 0 }}
              whileInView={{ height: `${(xg[index] / max) * 100}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: index * 0.06 }}
              title={`xG ${xg[index].toFixed(2)}`}
            />
            <motion.div
              className="relative w-3/5 rounded-t-md"
              style={{
                background: index === best && goals[index] > 0 ? "#9ccfea" : color,
              }}
              initial={{ height: 0 }}
              whileInView={{ height: `${(goals[index] / max) * 100}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.1 + index * 0.06 }}
            />
          </div>
          <span className={`text-xs ${index === 5 ? "font-bold text-ink" : "text-muted"}`}>{label}</span>
        </div>
      ))}
    </div>
  );
}

function Stat({ value, label, highlight = false }: { value: string | number; label: string; highlight?: boolean }) {
  return (
    <div className="flex flex-col">
      <span className={`font-display text-3xl font-bold tabular-nums ${highlight ? "text-[#9ccfea]" : ""}`}>
        {value}
      </span>
      <span className="text-xs text-muted">{label}</span>
    </div>
  );
}

export function ShotProfile({ shots, color = "#9ccfea" }: { shots: PlayerShot[]; color?: string }) {
  if (shots.length === 0) return null;
  const summary = summarize(shots);
  const finishing = summary.npGoals - summary.npXg;
  const feet = (["RightFoot", "LeftFoot", "Head", "OtherBodyPart"] as const)
    .map((key) => ({ key, ...summary.body[key] }))
    .filter((part) => part.shots > 0);
  const deadliest = [...feet].sort((a, b) => b.goals - a.goals)[0];

  return (
    <section className="glass grid grid-cols-1 gap-8 rounded-lg p-6 lg:grid-cols-[1.1fr_1fr]">
      <div className="flex flex-col gap-3">
        <div>
          <h2 className="font-display text-2xl font-bold tracking-tight">Mapa de tiros</h2>
          <p className="text-sm text-muted">
            {summary.shots} tiros, {summary.goals} goles. Los goles decisivos llevan borde grueso.
          </p>
        </div>
        <ShotMap shots={shots} color={color} />
      </div>

      <div className="flex flex-col gap-6">
        <div>
          <h3 className="mb-1 font-display text-lg font-bold">¿Cuándo marca?</h3>
          <p className="mb-3 text-xs text-muted">
            Barras = goles por tramo · contorno punteado = xG (lo que &quot;debería&quot; haber marcado).
          </p>
          <MinuteChart goals={summary.goalsByBucket} xg={summary.xgByBucket} color={color} />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <Stat value={summary.lateGoals} label="Goles 75'+" highlight={summary.lateGoals >= 3} />
          <Stat value={summary.decisiveGoals} label="Goles decisivos" />
          <Stat
            value={`${finishing >= 0 ? "+" : ""}${finishing.toFixed(1)}`}
            label="Goles vs xG"
            highlight={finishing >= 2}
          />
          <Stat value={summary.outsideBoxGoals} label="Desde fuera" />
          <Stat value={summary.headedGoals} label="De cabeza" />
          <Stat
            value={summary.npShots ? (summary.npXg / summary.npShots).toFixed(2) : "—"}
            label="xG por tiro"
          />
        </div>

        {feet.length > 0 && (
          <div>
            <h3 className="mb-2 flex items-center gap-2 font-display text-lg font-bold">
              Con qué la mete
              {deadliest && deadliest.goals > 0 && (
                <ScoutNote rotate={-3} className="text-base">
                  letal con {BODY_LABEL[deadliest.key].toLowerCase()}
                </ScoutNote>
              )}
            </h3>
            <ul className="flex flex-col gap-2">
              {feet.map((part) => (
                <li key={part.key} className="grid grid-cols-[110px_1fr_70px] items-center gap-3 text-sm">
                  <span className="text-ink/85">{BODY_LABEL[part.key]}</span>
                  <div className="h-2.5 overflow-hidden rounded-full bg-white/5">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: color }}
                      initial={{ width: 0 }}
                      whileInView={{ width: `${(part.shots / summary.shots) * 100}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.8 }}
                    />
                  </div>
                  <span className="text-right text-xs tabular-nums text-muted">
                    {part.goals} g / {part.shots} t
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
