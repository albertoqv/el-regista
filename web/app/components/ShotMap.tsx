"use client";

import { motion } from "motion/react";
import { useState } from "react";
import type { PlayerShot } from "@/lib/api";

// Half pitch, attacking upwards: 68 m wide x 52.5 m deep, 10 px per metre.
const W = 680;
const H = 525;

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

/** Understat x runs towards goal (0-1 over 105 m), y across (0-1 over 68 m). */
function toSvg(shot: PlayerShot) {
  return {
    cx: round(shot.y * W),
    cy: round((1 - shot.x) * 1050),
  };
}

const RESULT_LABEL: Record<string, string> = {
  Goal: "Gol",
  SavedShot: "Parado",
  MissedShot: "Fuera",
  BlockedShot: "Bloqueado",
  ShotOnPost: "Al palo",
  OwnGoal: "Autogol",
};

export function ShotMap({ shots, color = "#3d8bff" }: { shots: PlayerShot[]; color?: string }) {
  const [hovered, setHovered] = useState<number | null>(null);
  const visible = shots.filter((shot) => shot.x >= 0.5 && shot.result !== "OwnGoal");
  const active = hovered !== null ? visible[hovered] : null;

  return (
    <div className="relative">
      <svg viewBox={`-10 -10 ${W + 20} ${H + 20}`} className="h-auto w-full" role="img" aria-label="Mapa de tiros">
        <g fill="none" stroke="rgba(226,232,255,0.22)" strokeWidth="2" strokeDasharray="30 3 18 2">
          <rect x="0" y="0" width={W} height={H} rx="4" />
          <rect x={W / 2 - 201.6} y="0" width="403.2" height="165" />
          <rect x={W / 2 - 91.6} y="0" width="183.2" height="55" />
          {/* The "D": arc of 9.15 m around the penalty spot, outside the box. */}
          <path d={`M ${W / 2 - 73.1} 165 A 91.5 91.5 0 0 0 ${W / 2 + 73.1} 165`} />
          <path d={`M ${W / 2 - 91.5} ${H} A 91.5 91.5 0 0 1 ${W / 2 + 91.5} ${H}`} />
          <line x1={W / 2 - 36.6} y1="-6" x2={W / 2 + 36.6} y2="-6" strokeWidth="5" strokeDasharray="none" stroke="rgba(255,255,255,0.5)" />
        </g>
        <circle cx={W / 2} cy="110" r="3" fill="rgba(226,232,255,0.4)" />

        {visible.map((shot, index) => {
          const { cx, cy } = toSvg(shot);
          const goal = shot.result === "Goal";
          const radius = round(5 + Math.sqrt(shot.xg) * 26);
          return (
            <motion.circle
              key={`${shot.played_on}-${shot.minute}-${index}`}
              cx={cx}
              cy={cy}
              r={radius}
              initial={{ opacity: 0, scale: 0 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.012, type: "spring", stiffness: 220, damping: 16 }}
              style={{ transformOrigin: `${cx}px ${cy}px`, cursor: "pointer" }}
              fill={goal ? color : "transparent"}
              fillOpacity={goal ? 0.85 : 0}
              stroke={goal ? "#fff" : `${color}aa`}
              strokeWidth={goal ? (shot.decisive ? 3.5 : 1.5) : 1.5}
              onMouseEnter={() => setHovered(index)}
              onMouseLeave={() => setHovered(null)}
            />
          );
        })}
      </svg>
      <div className="mt-2 flex min-h-10 flex-wrap items-center justify-between gap-2 text-xs text-muted">
        {active ? (
          <span className="text-ink">
            <strong>{active.minute}&apos;</strong> vs {active.opponent} · {RESULT_LABEL[active.result] ?? active.result}
            {" · "}xG {active.xg.toFixed(2)}
            {active.decisive && " · gol decisivo"}
            {active.assisted_by && ` · asistencia de ${active.assisted_by}`}
          </span>
        ) : (
          <span>Pasa por encima de un tiro para ver el detalle.</span>
        )}
        <span className="flex items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full border border-white" style={{ background: color }} />
            gol
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full border" style={{ borderColor: color }} />
            tiro
          </span>
          <span>tamaño = xG</span>
        </span>
      </div>
    </div>
  );
}
