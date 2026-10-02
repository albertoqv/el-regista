"use client";

import { motion } from "motion/react";
import { CountUp } from "@/app/components/motion";

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function verdict(percentage: number): string {
  if (percentage >= 85) return "Casi gemelos";
  if (percentage >= 70) return "Muy parecidos";
  if (percentage >= 50) return "Algo en común";
  return "Perfiles distintos";
}

/** Animated ring gauge showing how alike two statistical profiles are. */
export function SimilarityMeter({
  percentage,
  size = 150,
}: {
  percentage: number;
  size?: number;
}) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
          <defs>
            <linearGradient id="similarity-gradient" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#c93c17" />
              <stop offset="100%" stopColor="#c93c17" />
            </linearGradient>
          </defs>
          <circle cx="60" cy="60" r={RADIUS} fill="none" stroke="rgba(22,23,27,0.07)" strokeWidth="9" />
          <motion.circle
            cx="60"
            cy="60"
            r={RADIUS}
            fill="none"
            stroke="url(#similarity-gradient)"
            strokeWidth="9"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            initial={{ strokeDashoffset: CIRCUMFERENCE }}
            whileInView={{
              strokeDashoffset: CIRCUMFERENCE * (1 - percentage / 100),
            }}
            viewport={{ once: true }}
            transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-4xl font-bold tabular-nums">
            <CountUp value={percentage} />
            <span className="text-xl text-muted">%</span>
          </span>
          <span className="text-xs font-semibold text-muted">
            similitud
          </span>
        </div>
      </div>
      <span className="text-sm font-medium text-ink/80">{verdict(percentage)}</span>
    </div>
  );
}
