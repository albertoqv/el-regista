import type { PlayerTrend } from "@/lib/api";

const W = 720;
const H = 220;
const PAD = { top: 16, right: 12, bottom: 12, left: 44 };

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

function number(value: number, decimals = 2): string {
  return value.toFixed(decimals).replace(".", ",");
}

const DIRECTION = {
  up: "Al alza",
  down: "A la baja",
  steady: "Estable",
} as const;

/** One line in plain words: where his form is going and how he finishes. */
function summary(trend: PlayerTrend): string | null {
  const parts: string[] = [];
  if (trend.direction && trend.recent_per90 !== null && trend.earlier_per90 !== null) {
    parts.push(
      `${DIRECTION[trend.direction]}: ${number(trend.recent_per90)} xG+xA por 90 en los últimos ${trend.window} partidos, ${number(trend.earlier_per90)} antes.`,
    );
  }
  if (Math.abs(trend.goals_minus_xg) >= 1) {
    const sign = trend.goals_minus_xg > 0 ? "por encima" : "por debajo";
    parts.push(`Marca ${number(Math.abs(trend.goals_minus_xg), 1)} goles ${sign} de su xG.`);
  }
  return parts.length ? parts.join(" ") : null;
}

/** xG + xA of each match (bars) and its rolling level per 90 (line). */
export function TrendChart({ trend }: { trend: PlayerTrend }) {
  const matches = trend.matches;
  if (matches.length < 3) return null;
  const values = matches.map((m) => m.xg + m.xa);
  const max = Math.max(...values, ...matches.map((m) => m.rolling_per90), 0.5);
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const slot = plotW / matches.length;
  const bar = Math.max(2, Math.min(slot - 2, 18));
  const x = (index: number) => round(PAD.left + slot * index + slot / 2);
  const y = (value: number) => round(PAD.top + plotH - (value / max) * plotH);
  const ticks = [0, max / 2, max].map((tick) => Math.round(tick * 10) / 10);
  const line = matches.map((m, index) => `${index ? "L" : "M"}${x(index)},${y(m.rolling_per90)}`).join(" ");
  const text = summary(trend);

  return (
    <section className="flex flex-col gap-3">
      <div>
        <h2 className="font-heading text-2xl tracking-tight">Tendencia</h2>
        {text && <p className="text-sm text-muted">{text}</p>}
      </div>
      {/* Axis numbers in HTML: they keep their size when the chart shrinks on a phone. */}
      <div className="relative">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="Amenaza por partido y su media móvil">
          {ticks.map((tick) => (
            <line key={tick} x1={PAD.left} x2={W - PAD.right} y1={y(tick)} y2={y(tick)} stroke="rgba(22,23,27,0.08)" />
          ))}
          {matches.map((m, index) => {
            const value = values[index];
            const top = y(value);
            const height = round(PAD.top + plotH - top);
            return (
              <g key={`${m.played_on}-${m.opponent}`}>
                <rect x={round(x(index) - bar / 2)} y={top} width={round(bar)} height={Math.max(height, 1)} rx="3" fill="rgba(22,23,27,0.22)" />
                {m.goals + m.assists > 0 && (
                  <circle cx={x(index)} cy={round(top - 7)} r="4" fill="#16171b" stroke="#f7f6f2" strokeWidth="2" />
                )}
                <rect x={round(x(index) - slot / 2)} y={PAD.top} width={round(slot)} height={plotH} fill="transparent">
                  <title>{`${m.played_on} ${m.home ? "vs" : "en"} ${m.opponent}: ${m.minutes}' · ${m.goals} G · ${m.assists} A · xG ${number(m.xg)} · xA ${number(m.xa)}`}</title>
                </rect>
              </g>
            );
          })}
          <path d={line} fill="none" stroke="#c93c17" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        </svg>
        {ticks.map((tick) => (
          <span
            key={tick}
            className="absolute left-0 -translate-y-1/2 text-xs tabular-nums text-muted"
            style={{ top: `${round((y(tick) / H) * 100)}%` }}
          >
            {number(tick, 1)}
          </span>
        ))}
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm bg-ink/20" /> xG + xA del partido
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4 bg-brand" /> Media de {trend.window} partidos, por 90
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-ink" /> Marcó o asistió
        </span>
      </div>
    </section>
  );
}
