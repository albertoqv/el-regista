"use client";

import { motion } from "motion/react";
import { METRICS, type MetricKey } from "@/lib/metrics";

export type RadarSeries = {
  name: string;
  color: string;
  /** Percentile (0-100) per metric; metrics without data are skipped. */
  values: Partial<Record<MetricKey, number>>;
};

const SIZE = 420;
const CENTER = SIZE / 2;
const RADIUS = 150;
const RINGS = [25, 50, 75, 100];

function point(index: number, total: number, value: number) {
  const angle = (Math.PI * 2 * index) / total - Math.PI / 2;
  const distance = (value / 100) * RADIUS;
  // Rounded: server and browser trig differ in the last decimals (hydration).
  return {
    x: Math.round((CENTER + Math.cos(angle) * distance) * 100) / 100,
    y: Math.round((CENTER + Math.sin(angle) * distance) * 100) / 100,
  };
}

export function RadarChart({
  axes,
  series,
}: {
  axes: MetricKey[];
  series: RadarSeries[];
}) {
  const shown = axes.filter((axis) =>
    series.some((entry) => entry.values[axis] !== undefined),
  );
  if (shown.length < 3) {
    return (
      <p className="py-10 text-center text-sm text-muted">
        No hay suficientes métricas en esta temporada para dibujar el radar.
      </p>
    );
  }
  const total = shown.length;

  return (
    <svg
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      className="mx-auto h-auto w-full max-w-[460px] overflow-visible"
      role="img"
      aria-label="Radar de percentiles"
    >
      <defs>
        {series.map((entry, index) => (
          <radialGradient key={entry.name} id={`radar-fill-${index}`}>
            <stop offset="0%" stopColor={entry.color} stopOpacity="0.05" />
            <stop offset="100%" stopColor={entry.color} stopOpacity="0.35" />
          </radialGradient>
        ))}
      </defs>

      {RINGS.map((ring) => (
        <polygon
          key={ring}
          points={shown
            .map((_, index) => {
              const p = point(index, total, ring);
              return `${p.x},${p.y}`;
            })
            .join(" ")}
          fill={ring === 100 ? "rgba(22,23,27,0.02)" : "none"}
          stroke="rgba(22,23,27,0.08)"
          strokeDasharray={ring === 50 ? "4 4" : undefined}
        />
      ))}

      {shown.map((axis, index) => {
        const end = point(index, total, 100);
        const label = point(index, total, 122);
        const anchor =
          Math.abs(label.x - CENTER) < 12 ? "middle" : label.x > CENTER ? "start" : "end";
        return (
          <g key={axis}>
            <line
              x1={CENTER}
              y1={CENTER}
              x2={end.x}
              y2={end.y}
              stroke="rgba(22,23,27,0.07)"
            />
            <text
              x={label.x}
              y={label.y}
              textAnchor={anchor}
              dominantBaseline="middle"
              className="fill-[#5d6068] text-[12px] font-medium"
            >
              <title>{METRICS[axis].help}</title>
              {METRICS[axis].short}
            </text>
          </g>
        );
      })}

      {series.map((entry, seriesIndex) => {
        const coords = shown.map((axis, index) =>
          point(index, total, Math.max(entry.values[axis] ?? 0, 3)),
        );
        const polygon = coords.map((p) => `${p.x},${p.y}`).join(" ");
        return (
          <motion.g
            key={entry.name}
            initial={{ scale: 0, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{
              duration: 0.9,
              delay: 0.15 + seriesIndex * 0.2,
              ease: [0.22, 1, 0.36, 1],
            }}
            style={{ transformOrigin: `${CENTER}px ${CENTER}px` }}
          >
            <polygon
              points={polygon}
              fill={`url(#radar-fill-${seriesIndex})`}
              stroke={entry.color}
              strokeWidth={2.5}
              strokeLinejoin="round"
            />
            {coords.map((p, index) => (
              <circle
                key={shown[index]}
                cx={p.x}
                cy={p.y}
                r={3.5}
                fill="#ffffff"
                stroke={entry.color}
                strokeWidth={2}
              >
                <title>
                  {`${entry.name} · ${METRICS[shown[index]].label}: percentil ${entry.values[shown[index]] ?? "sin datos"}`}
                </title>
              </circle>
            ))}
          </motion.g>
        );
      })}
    </svg>
  );
}
