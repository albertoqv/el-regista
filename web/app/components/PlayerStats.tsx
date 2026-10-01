"use client";

import { useState } from "react";
import { CountUp, Reveal } from "@/app/components/motion";
import type { Player } from "@/lib/api";
import { GROUPS, METRICS, metricValue } from "@/lib/metrics";

export function PlayerStats({ player }: { player: Player }) {
  const [perNinety, setPerNinety] = useState(false);
  const canPerNinety = player.minutes_played > 0;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-display text-2xl font-bold tracking-tight">Estadísticas</h2>
        {canPerNinety && (
          <div className="glass flex rounded-full p-1 text-xs font-semibold">
            {[
              { value: false, label: "Totales" },
              { value: true, label: "Por 90'" },
            ].map((option) => (
              <button
                key={option.label}
                type="button"
                onClick={() => setPerNinety(option.value)}
                className={`rounded-full px-3 py-1.5 transition ${perNinety === option.value ? "bg-white text-bg" : "text-muted hover:text-ink"}`}
              >
                {option.label}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {GROUPS.map((group, groupIndex) => {
          const metrics = group.metrics.filter(
            (key) => player[key] > 0 || !["passes_completed", "dribbles_completed", "expected_goals", "expected_assists", "xg_chain", "xg_buildup"].includes(key),
          );
          return (
            <Reveal key={group.key} delay={groupIndex * 0.06}>
              <div className="glass h-full rounded-lg p-5">
                <h3 className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-muted">
                  {group.title}
                </h3>
                <div className="grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-3">
                  {metrics.map((key) => {
                    const info = METRICS[key];
                    const value = metricValue(player, key, perNinety);
                    return (
                      <div key={key} className="flex flex-col" title={info.help}>
                        <span className="font-display text-3xl font-bold tabular-nums">
                          <CountUp
                            key={String(perNinety)}
                            value={value}
                            decimals={perNinety ? 2 : (info.decimals ?? 0)}
                            duration={0.8}
                          />
                        </span>
                        <span className="text-xs text-muted">{info.short}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </Reveal>
          );
        })}
      </div>
    </div>
  );
}
