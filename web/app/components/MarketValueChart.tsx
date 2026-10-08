"use client";

import { motion } from "motion/react";
import { useState, type PointerEvent } from "react";
import type { MarketValuePoint } from "@/lib/api";
import { formatMarketValue } from "@/lib/format";

const WIDTH = 720;
const HEIGHT = 240;
const PAD_X = 16;
const PAD_Y = 24;
// Year labels: at most this many, evenly spread.
const MAX_YEAR_LABELS = 9;

export type ValueSeries = {
  name: string;
  color: string;
  history: MarketValuePoint[];
};

function time(point: MarketValuePoint): number {
  return new Date(point.as_of).getTime();
}

// Server-computed SVG: round so the markup matches after hydration.
function round(value: number): number {
  return Math.round(value * 10) / 10;
}

/** The valuation closest in time to `at`, within the player's own history. */
function nearest(history: MarketValuePoint[], at: number): MarketValuePoint {
  return history.reduce((best, point) =>
    Math.abs(time(point) - at) < Math.abs(time(best) - at) ? point : best,
  );
}

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-ES", { month: "short", year: "numeric" });
}

/** Market value over time; several players share the same axes. Hover or touch
 * the chart to read each player's value at that moment. */
export function MarketValueChart({ series }: { series: ValueSeries[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const withData = series.filter((entry) => entry.history.length > 0);
  if (withData.length === 0) return null;

  const points = withData.flatMap((entry) => entry.history);
  const minTime = Math.min(...points.map(time));
  const maxTime = Math.max(...points.map(time));
  const span = maxTime - minTime || 1;
  const maxAmount = Math.max(...points.map((point) => point.amount_eur), 1);

  const xAt = (at: number) => round(PAD_X + ((at - minTime) / span) * (WIDTH - PAD_X * 2));
  const x = (point: MarketValuePoint) => xAt(time(point));
  const y = (point: MarketValuePoint) => round(PAD_Y + (1 - point.amount_eur / maxAmount) * (HEIGHT - PAD_Y * 2));

  const firstYear = new Date(minTime).getFullYear();
  const lastYear = new Date(maxTime).getFullYear();
  const step = Math.max(1, Math.ceil((lastYear - firstYear + 1) / MAX_YEAR_LABELS));
  const years: number[] = [];
  for (let year = firstYear + 1; year <= lastYear; year += step) years.push(year);

  function track(event: PointerEvent<SVGSVGElement>) {
    const box = event.currentTarget.getBoundingClientRect();
    const ratio = ((event.clientX - box.left) / box.width) * WIDTH;
    const clamped = Math.min(Math.max(ratio, PAD_X), WIDTH - PAD_X);
    setHover(minTime + ((clamped - PAD_X) / (WIDTH - PAD_X * 2)) * span);
  }

  return (
    <div className="glass rounded-lg p-5">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-3">
        <h3 className="font-heading text-lg tracking-tight">Valor de mercado</h3>
        <div className="flex flex-wrap gap-4">
          {withData.map((entry) => {
            const latest = entry.history[entry.history.length - 1];
            const peak = Math.max(...entry.history.map((point) => point.amount_eur));
            const shown = hover === null ? latest : nearest(entry.history, hover);
            return (
              <div key={entry.name} className="flex flex-col items-end">
                <span className="font-heading text-2xl tabular-nums" style={{ color: entry.color }}>
                  {formatMarketValue(shown.amount_eur)}
                </span>
                <span className="text-xs text-muted">
                  {withData.length > 1 ? `${entry.name} · ` : ""}
                  {hover === null
                    ? `hoy · máximo ${formatMarketValue(peak)}`
                    : `${shortDate(shown.as_of)}${shown.club ? ` · ${shown.club}` : ""}`}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="relative">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="h-auto w-full touch-pan-y"
          role="img"
          aria-label="Evolución del valor de mercado: pasa el dedo o el ratón para ver cada fecha"
          onPointerMove={track}
          onPointerDown={track}
          onPointerLeave={() => setHover(null)}
        >
          {[0.25, 0.5, 0.75].map((ratio) => (
            <line
              key={ratio}
              x1={PAD_X}
              x2={WIDTH - PAD_X}
              y1={round(PAD_Y + ratio * (HEIGHT - PAD_Y * 2))}
              y2={round(PAD_Y + ratio * (HEIGHT - PAD_Y * 2))}
              stroke="rgba(22,23,27,0.06)"
            />
          ))}
          {years.map((year) => (
            <line
              key={year}
              x1={xAt(new Date(`${year}-01-01`).getTime())}
              x2={xAt(new Date(`${year}-01-01`).getTime())}
              y1={PAD_Y}
              y2={HEIGHT - PAD_Y}
              stroke="rgba(22,23,27,0.05)"
            />
          ))}
          {withData.map((entry) => {
            const line = entry.history.map((point, i) => `${i === 0 ? "M" : "L"} ${x(point)} ${y(point)}`).join(" ");
            const first = entry.history[0];
            const last = entry.history[entry.history.length - 1];
            const area = `${line} L ${x(last)} ${HEIGHT - PAD_Y} L ${x(first)} ${HEIGHT - PAD_Y} Z`;
            return (
              <g key={entry.name}>
                <motion.path
                  d={area}
                  fill={entry.color}
                  fillOpacity={0.08}
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 1, delay: 0.6 }}
                />
                <motion.path
                  d={line}
                  fill="none"
                  stroke={entry.color}
                  strokeWidth={2.5}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  initial={{ pathLength: 0 }}
                  whileInView={{ pathLength: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 1.6, ease: "easeInOut" }}
                />
                {hover === null ? (
                  <circle cx={x(last)} cy={y(last)} r={4.5} fill={entry.color} />
                ) : (
                  <circle
                    cx={x(nearest(entry.history, hover))}
                    cy={y(nearest(entry.history, hover))}
                    r={5}
                    fill={entry.color}
                    stroke="#f7f6f2"
                    strokeWidth={2}
                  />
                )}
              </g>
            );
          })}
          {hover !== null && (
            <line x1={xAt(hover)} x2={xAt(hover)} y1={PAD_Y / 2} y2={HEIGHT - PAD_Y} stroke="rgba(22,23,27,0.35)" />
          )}
        </svg>
        {years.map((year) => (
          <span
            key={year}
            className="absolute -bottom-1 -translate-x-1/2 text-xs tabular-nums text-muted"
            style={{ left: `${round((xAt(new Date(`${year}-01-01`).getTime()) / WIDTH) * 100)}%` }}
          >
            {year}
          </span>
        ))}
      </div>
      <p className="mt-4 text-xs text-muted">Pasa el ratón o el dedo por la gráfica para ver el valor de cada fecha.</p>
    </div>
  );
}
