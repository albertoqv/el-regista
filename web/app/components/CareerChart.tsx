import type { CareerCurve } from "@/lib/api";
import { positionLabel, seasonDisplay } from "@/lib/format";

const W = 720;
const H = 220;
const PAD = { top: 16, right: 16, bottom: 28, left: 44 };
// Ages with fewer players than this make a jumpy reference line.
const MINIMUM_PEERS = 8;

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

function number(value: number, decimals = 2): string {
  return value.toFixed(decimals).replace(".", ",");
}

/** His last season against his position's level at that age, in plain words. */
function summary(curve: CareerCurve, peers: Map<number, number>, position: string): string | null {
  const last = curve.points[curve.points.length - 1];
  const reference = peers.get(last.age);
  if (!reference) return null;
  const ratio = last.per90 / reference;
  const how =
    ratio >= 1.15 ? `${number(ratio, 1)} veces la media` : ratio <= 0.85 ? "por debajo de la media" : "en la media";
  return `En ${seasonDisplay(last.season_label)}, con ${last.age} años: ${number(last.per90)} goles + asistencias por 90, ${how} de los ${position} de su edad (${number(reference)}).`;
}

/** Goals + assists per 90 at each age of his career, over his position's average. */
export function CareerChart({ curve, color }: { curve: CareerCurve; color: string }) {
  if (curve.points.length < 2) return null;
  const position = `${positionLabel(curve.position).toLowerCase()}s`;
  const peers = new Map(
    curve.benchmark.filter((point) => point.players >= MINIMUM_PEERS).map((point) => [point.age, point.per90]),
  );
  const first = curve.points[0].age - 1;
  const last = curve.points[curve.points.length - 1].age + 1;
  const ages = Array.from({ length: last - first + 1 }, (_, index) => first + index);
  const reference = ages.filter((age) => peers.has(age));
  const max = Math.max(0.4, ...curve.points.map((p) => p.per90), ...reference.map((age) => peers.get(age) ?? 0));
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const x = (age: number) => round(PAD.left + ((age - first) / (last - first)) * plotW);
  const y = (value: number) => round(PAD.top + plotH - (value / max) * plotH);
  const path = (points: [number, number][]) =>
    points.map(([age, value], index) => `${index ? "L" : "M"}${x(age)},${y(value)}`).join(" ");
  const ticks = [0, max / 2, max].map((tick) => Math.round(tick * 100) / 100);
  const text = summary(curve, peers, position);

  return (
    <section className="flex flex-col gap-3">
      <div>
        <h2 className="font-heading text-2xl tracking-tight">Su carrera por edad</h2>
        {text && <p className="text-sm text-muted">{text}</p>}
      </div>
      {/* Axis numbers in HTML: they keep their size when the chart shrinks on a phone. */}
      <div className="relative">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label="Goles y asistencias por 90 según la edad">
          {ticks.map((tick) => (
            <line key={tick} x1={PAD.left} x2={W - PAD.right} y1={y(tick)} y2={y(tick)} stroke="rgba(22,23,27,0.08)" />
          ))}
          {reference.length > 1 && (
            <path
              d={path(reference.map((age) => [age, peers.get(age) ?? 0]))}
              fill="none"
              stroke="rgba(22,23,27,0.35)"
              strokeWidth="2"
              strokeDasharray="6 5"
            />
          )}
          <path
            d={path(curve.points.map((point) => [point.age, point.per90]))}
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {curve.points.map((point) => (
            <circle key={point.season_label} cx={x(point.age)} cy={y(point.per90)} r="5" fill={color} stroke="#f7f6f2" strokeWidth="2">
              <title>{`${seasonDisplay(point.season_label)} (${point.age} años): ${point.goals} goles y ${point.assists} asistencias en ${point.minutes_played} minutos`}</title>
            </circle>
          ))}
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
        {ages.map((age) => (
          <span
            key={age}
            className="absolute bottom-0 -translate-x-1/2 text-xs tabular-nums text-muted"
            style={{ left: `${round((x(age) / W) * 100)}%` }}
          >
            {age}
          </span>
        ))}
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4" style={{ background: color }} /> Goles + asistencias por 90, con el club
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4 bg-ink/35" /> Media de los {position} a cada edad
        </span>
      </div>
    </section>
  );
}
