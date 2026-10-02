import { PROFILE_LABELS, PROFILE_ORDER } from "@/lib/metrics";

const SIZE = 150;
const C = SIZE / 2;
const R = 58;

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function point(index: number, total: number, value: number) {
  const angle = (Math.PI * 2 * index) / total - Math.PI / 2;
  return { x: round(C + Math.cos(angle) * (value / 100) * R), y: round(C + Math.sin(angle) * (value / 100) * R) };
}

/** Two percentile profiles on top of each other: target (white) and twin (gold). */
export function MiniRadar({
  target,
  twin,
}: {
  target: Record<string, number>;
  twin: Record<string, number>;
}) {
  const axes = PROFILE_ORDER.filter((key) => key in target && key in twin);
  if (axes.length < 5) return null;
  const polygon = (values: Record<string, number>) =>
    axes
      .map((key, index) => {
        const p = point(index, axes.length, Math.max(values[key], 4));
        return `${p.x},${p.y}`;
      })
      .join(" ");

  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="h-28 w-28 shrink-0" role="img" aria-label="Perfil superpuesto">
      <title>{`Blanco: el jugador buscado · Dorado: el gemelo (${axes.map((key) => PROFILE_LABELS[key] ?? key).join(", ")})`}</title>
      {[50, 100].map((ring) => (
        <polygon
          key={ring}
          points={axes
            .map((_, index) => {
              const p = point(index, axes.length, ring);
              return `${p.x},${p.y}`;
            })
            .join(" ")}
          fill="none"
          stroke="rgba(22,23,27,0.1)"
        />
      ))}
      <polygon points={polygon(target)} fill="rgba(22,23,27,0.08)" stroke="rgba(22,23,27,0.8)" strokeWidth="1.5" />
      <polygon points={polygon(twin)} fill="rgba(35,80,216,0.25)" stroke="#2350d8" strokeWidth="1.5" />
    </svg>
  );
}
