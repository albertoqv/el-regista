"use client";

import { motion } from "motion/react";
import type { MarketValuePoint } from "@/lib/api";
import { formatMarketValue } from "@/lib/format";

const WIDTH = 720;
const HEIGHT = 240;
const PAD_X = 16;
const PAD_Y = 24;

export type ValueSeries = {
  name: string;
  color: string;
  history: MarketValuePoint[];
};

function time(point: MarketValuePoint): number {
  return new Date(point.as_of).getTime();
}

/** Market value over time; several players share the same axes. */
export function MarketValueChart({ series }: { series: ValueSeries[] }) {
  const withData = series.filter((entry) => entry.history.length > 0);
  if (withData.length === 0) return null;

  const points = withData.flatMap((entry) => entry.history);
  const minTime = Math.min(...points.map(time));
  const maxTime = Math.max(...points.map(time));
  const maxAmount = Math.max(...points.map((point) => point.amount_eur), 1);

  const x = (point: MarketValuePoint) =>
    PAD_X + ((time(point) - minTime) / (maxTime - minTime || 1)) * (WIDTH - PAD_X * 2);
  const y = (point: MarketValuePoint) =>
    PAD_Y + (1 - point.amount_eur / maxAmount) * (HEIGHT - PAD_Y * 2);

  const firstYear = new Date(minTime).getFullYear();
  const lastYear = new Date(maxTime).getFullYear();

  return (
    <div className="glass rounded-3xl p-5">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-3">
        <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">
          Valor de mercado
        </h3>
        <div className="flex flex-wrap gap-4">
          {withData.map((entry) => {
            const latest = entry.history[entry.history.length - 1];
            const peak = Math.max(...entry.history.map((point) => point.amount_eur));
            return (
              <div key={entry.name} className="flex flex-col items-end">
                <span className="font-display text-2xl font-bold" style={{ color: entry.color }}>
                  {formatMarketValue(latest.amount_eur)}
                </span>
                <span className="text-[11px] text-muted">
                  {withData.length > 1 ? `${entry.name} · ` : ""}máximo {formatMarketValue(peak)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-auto w-full" role="img" aria-label="Evolución del valor de mercado">
        <defs>
          {withData.map((entry, index) => (
            <linearGradient key={entry.name} id={`value-area-${index}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={entry.color} stopOpacity="0.35" />
              <stop offset="100%" stopColor={entry.color} stopOpacity="0" />
            </linearGradient>
          ))}
        </defs>
        {[0.25, 0.5, 0.75].map((ratio) => (
          <line
            key={ratio}
            x1={PAD_X}
            x2={WIDTH - PAD_X}
            y1={PAD_Y + ratio * (HEIGHT - PAD_Y * 2)}
            y2={PAD_Y + ratio * (HEIGHT - PAD_Y * 2)}
            stroke="rgba(255,255,255,0.05)"
          />
        ))}
        {withData.map((entry, index) => {
          const line = entry.history
            .map((point, i) => `${i === 0 ? "M" : "L"} ${x(point)} ${y(point)}`)
            .join(" ");
          const first = entry.history[0];
          const last = entry.history[entry.history.length - 1];
          const area = `${line} L ${x(last)} ${HEIGHT - PAD_Y} L ${x(first)} ${HEIGHT - PAD_Y} Z`;
          return (
            <g key={entry.name}>
              <motion.path
                d={area}
                fill={`url(#value-area-${index})`}
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
                style={{ filter: `drop-shadow(0 0 6px ${entry.color})` }}
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1.6, ease: "easeInOut" }}
              />
              {entry.history.map((point) => (
                <circle key={point.as_of} cx={x(point)} cy={y(point)} r={9} fill="transparent">
                  <title>
                    {`${entry.name} · ${point.as_of} · ${point.club} · ${formatMarketValue(point.amount_eur)}`}
                  </title>
                </circle>
              ))}
              <circle cx={x(last)} cy={y(last)} r={4.5} fill={entry.color} />
            </g>
          );
        })}
      </svg>
      <div className="flex justify-between text-xs text-muted">
        <span>{firstYear}</span>
        <span>{lastYear}</span>
      </div>
    </div>
  );
}
