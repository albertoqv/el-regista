"use client";

import { motion } from "motion/react";
import { useState } from "react";
import type { Twin, TwinProfile } from "@/lib/api";
import { bigPhoto, formatMarketValue } from "@/lib/format";

const WIDTH = 900;
const HEIGHT = 380;
const PAD = { left: 56, right: 24, top: 24, bottom: 44 };
const R = 17;

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

/**
 * Price (x, log scale) against similarity (y). The best signings sit top-left:
 * very alike and cheap.
 */
export function ValueMap({ target, twins }: { target: TwinProfile; twins: Twin[] }) {
  const [hovered, setHovered] = useState<number | null>(null);
  const priced = twins.filter((twin) => twin.market_value_eur !== null && twin.market_value_eur > 0);
  if (priced.length < 3) return null;

  const values = priced.map((twin) => twin.market_value_eur as number);
  if (target.market_value_eur) values.push(target.market_value_eur);
  const minLog = Math.log10(Math.min(...values) / 1.6);
  const maxLog = Math.log10(Math.max(...values) * 1.4);
  const minSimilarity = Math.max(0, Math.min(...priced.map((twin) => twin.similarity)) - 4);

  const x = (value: number) =>
    round(PAD.left + ((Math.log10(value) - minLog) / (maxLog - minLog)) * (WIDTH - PAD.left - PAD.right));
  const y = (similarity: number) =>
    round(PAD.top + (1 - (similarity - minSimilarity) / (100 - minSimilarity)) * (HEIGHT - PAD.top - PAD.bottom));

  const ticks = [1e6, 5e6, 1e7, 2.5e7, 5e7, 1e8, 2e8].filter(
    (tick) => Math.log10(tick) > minLog && Math.log10(tick) < maxLog,
  );
  const active = priced.find((twin) => twin.player_id === hovered);

  return (
    <div className="glass relative rounded-lg p-4 sm:p-6">
      <div className="mb-2 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="font-display text-xl font-bold tracking-tight">Mapa de fichajes</h2>
          <p className="text-sm text-muted">
            Arriba = más parecido · izquierda = más barato. Lo ideal está arriba a la izquierda.
          </p>
        </div>
        {active && (
          <p className="text-sm">
            <span className="font-semibold">{active.name}</span>{" "}
            <span className="text-muted">
              {active.similarity}% · {formatMarketValue(active.market_value_eur as number)}
            </span>
          </p>
        )}
      </div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-auto w-full" role="img" aria-label="Precio frente a parecido">
        <defs>
          {priced.map((twin) => (
            <clipPath key={twin.player_id} id={`dot-${twin.player_id}`}>
              <circle cx={x(twin.market_value_eur as number)} cy={y(twin.similarity)} r={R} />
            </clipPath>
          ))}
        </defs>

        <rect
          x={PAD.left}
          y={PAD.top}
          width={round((WIDTH - PAD.left - PAD.right) * 0.42)}
          height={round((HEIGHT - PAD.top - PAD.bottom) * 0.45)}
          rx="14"
          fill="rgba(255,215,106,0.05)"
          stroke="rgba(255,215,106,0.25)"
          strokeDasharray="6 6"
        />
        <text x={PAD.left + 12} y={PAD.top + 30} className="fill-[#f2c230] font-hand text-[26px]">
          zona ganga
        </text>

        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={x(tick)} x2={x(tick)} y1={PAD.top} y2={HEIGHT - PAD.bottom} stroke="rgba(255,255,255,0.05)" />
            <text x={x(tick)} y={HEIGHT - 16} textAnchor="middle" className="fill-[#8b93a7] text-[12px]">
              {formatMarketValue(tick)}
            </text>
          </g>
        ))}
        {[minSimilarity, (minSimilarity + 100) / 2, 100].map((tick) => (
          <text key={tick} x={PAD.left - 10} y={y(tick) + 4} textAnchor="end" className="fill-[#8b93a7] text-[12px]">
            {Math.round(tick)}%
          </text>
        ))}

        {target.market_value_eur && (
          <g>
            <line
              x1={x(target.market_value_eur)}
              x2={x(target.market_value_eur)}
              y1={PAD.top}
              y2={HEIGHT - PAD.bottom}
              stroke="#ff8a4c"
              strokeDasharray="4 5"
              strokeWidth="1.5"
            />
            <text
              x={x(target.market_value_eur) - 8}
              y={PAD.top + 14}
              textAnchor="end"
              className="fill-[#ff9b78] text-[12px] font-semibold"
            >
              {target.name}: {formatMarketValue(target.market_value_eur)}
            </text>
          </g>
        )}

        {priced.map((twin, index) => {
          const cx = x(twin.market_value_eur as number);
          const cy = y(twin.similarity);
          const photo = bigPhoto(twin.photo_url);
          const isActive = hovered === twin.player_id;
          return (
            <a key={twin.player_id} href={`#twin-${twin.player_id}`}>
              <motion.g
                initial={{ opacity: 0, scale: 0.3 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 + index * 0.04, type: "spring", stiffness: 200, damping: 16 }}
                style={{ transformOrigin: `${cx}px ${cy}px`, cursor: "pointer" }}
                onMouseEnter={() => setHovered(twin.player_id)}
                onMouseLeave={() => setHovered(null)}
              >
                <circle cx={cx} cy={cy} r={R + 3} fill="#05070d" stroke={isActive ? "#f2c230" : "rgba(255,255,255,0.35)"} strokeWidth={isActive ? 3 : 1.5} />
                {photo ? (
                  <image
                    href={photo}
                    x={cx - R}
                    y={cy - R}
                    width={R * 2}
                    height={R * 2}
                    preserveAspectRatio="xMidYMin slice"
                    clipPath={`url(#dot-${twin.player_id})`}
                  />
                ) : (
                  <circle cx={cx} cy={cy} r={R} fill="#1d2a44" />
                )}
                <title>{`${twin.name} · ${twin.similarity}% · ${formatMarketValue(twin.market_value_eur as number)}`}</title>
              </motion.g>
            </a>
          );
        })}
      </svg>
    </div>
  );
}
