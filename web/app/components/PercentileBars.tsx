"use client";

import { motion } from "motion/react";
import type { PercentileReport } from "@/lib/api";
import { METRICS, RADAR_METRICS, percentileColor, type MetricKey } from "@/lib/metrics";

export function PercentileBars({ report }: { report: PercentileReport }) {
  const rows = RADAR_METRICS.filter((key) => report.metrics[key]);

  return (
    <ul className="flex flex-col gap-2.5">
      {rows.map((key: MetricKey, index) => {
        const { percentile, per_90 } = report.metrics[key];
        const color = percentileColor(percentile);
        return (
          <li key={key} className="group" title={METRICS[key].help}>
            <div className="mb-1 flex items-baseline justify-between gap-3 text-sm">
              <span className="text-ink/90">{METRICS[key].label}</span>
              <span className="flex items-baseline gap-2 tabular-nums">
                <span className="text-xs text-muted">{per_90.toFixed(2)} /90&apos;</span>
                <span className="w-8 text-right font-display font-bold" style={{ color }}>
                  {percentile}
                </span>
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-ink/6">
              <motion.div
                className="h-full rounded-full"
                style={{
                  background: `linear-gradient(90deg, ${color}66, ${color})`,
                }}
                initial={{ width: 0 }}
                whileInView={{ width: `${Math.max(percentile, 2)}%` }}
                viewport={{ once: true }}
                transition={{ duration: 0.9, delay: index * 0.04, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export function PercentileLegend() {
  const steps = [
    { label: "Élite (90+)", value: 95 },
    { label: "Muy bueno", value: 75 },
    { label: "Medio", value: 55 },
    { label: "Bajo", value: 35 },
    { label: "Muy bajo", value: 10 },
  ];
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
      {steps.map((step) => (
        <span key={step.label} className="flex items-center gap-1.5">
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: percentileColor(step.value) }}
          />
          {step.label}
        </span>
      ))}
    </div>
  );
}
