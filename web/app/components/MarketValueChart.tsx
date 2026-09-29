import type { MarketValuePoint } from "@/lib/api";

const LINE_COLOR = "#2a78d6";
const WIDTH = 640;
const HEIGHT = 200;
const PADDING = 32;

function formatAmount(amountEur: number): string {
  if (amountEur >= 1_000_000) {
    return `${(amountEur / 1_000_000).toFixed(amountEur % 1_000_000 === 0 ? 0 : 1)}M €`;
  }
  if (amountEur >= 1_000) {
    return `${(amountEur / 1_000).toFixed(0)}k €`;
  }
  return `${amountEur} €`;
}

export function MarketValueChart({ history }: { history: MarketValuePoint[] }) {
  if (history.length === 0) {
    return null;
  }

  const amounts = history.map((point) => point.amount_eur);
  const maxAmount = Math.max(...amounts);
  const minAmount = Math.min(0, ...amounts);
  const range = maxAmount - minAmount || 1;

  const innerWidth = WIDTH - PADDING * 2;
  const innerHeight = HEIGHT - PADDING * 2;

  const coords = history.map((point, index) => {
    const x =
      history.length === 1
        ? PADDING
        : PADDING + (index / (history.length - 1)) * innerWidth;
    const y = PADDING + innerHeight - ((point.amount_eur - minAmount) / range) * innerHeight;
    return { x, y, point };
  });

  const pathD = coords
    .map((coord, index) => `${index === 0 ? "M" : "L"} ${coord.x} ${coord.y}`)
    .join(" ");

  const latest = history[history.length - 1];

  return (
    <div className="flex flex-col gap-2 rounded-md border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
          Valor de mercado
        </h3>
        <span className="text-lg font-semibold" style={{ color: LINE_COLOR }}>
          {formatAmount(latest.amount_eur)}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="h-auto w-full"
        role="img"
        aria-label="Evolución del valor de mercado"
      >
        <path d={pathD} fill="none" stroke={LINE_COLOR} strokeWidth={2} />
        {coords.map((coord) => (
          <circle
            key={coord.point.as_of}
            cx={coord.x}
            cy={coord.y}
            r={3}
            fill={LINE_COLOR}
          >
            <title>
              {coord.point.as_of} · {coord.point.club} ·{" "}
              {formatAmount(coord.point.amount_eur)}
            </title>
          </circle>
        ))}
      </svg>
      <div className="flex justify-between text-xs text-zinc-500 dark:text-zinc-400">
        <span>
          {history[0].as_of} · {history[0].club}
        </span>
        <span>
          {latest.as_of} · {latest.club}
        </span>
      </div>
    </div>
  );
}
