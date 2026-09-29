import type { MarketValuePoint, PlayerSummary } from "@/lib/api";

const FOOT_LABELS: Record<string, string> = {
  left: "Zurdo",
  right: "Diestro",
  both: "Ambidiestro",
};

function formatAmount(amountEur: number): string {
  if (amountEur >= 1_000_000) {
    return `${(amountEur / 1_000_000).toFixed(amountEur % 1_000_000 === 0 ? 0 : 1)}M €`;
  }
  if (amountEur >= 1_000) {
    return `${(amountEur / 1_000).toFixed(0)}k €`;
  }
  return `${amountEur} €`;
}

export function PlayerBioCard({
  player,
  currentMarketValue,
}: {
  player: PlayerSummary;
  currentMarketValue: MarketValuePoint | null;
}) {
  if (!player.preferred_foot && !currentMarketValue) {
    return null;
  }

  return (
    <div className="flex gap-3">
      {player.preferred_foot && (
        <div className="flex flex-col gap-1 rounded-md border border-zinc-200 px-4 py-3 dark:border-zinc-800">
          <span className="text-xs text-zinc-500 dark:text-zinc-400">Pie</span>
          <span className="text-xl font-semibold">
            {FOOT_LABELS[player.preferred_foot] ?? player.preferred_foot}
          </span>
        </div>
      )}
      {currentMarketValue && (
        <div className="flex flex-col gap-1 rounded-md border border-zinc-200 px-4 py-3 dark:border-zinc-800">
          <span className="text-xs text-zinc-500 dark:text-zinc-400">
            Valor de mercado
          </span>
          <span className="text-xl font-semibold">
            {formatAmount(currentMarketValue.amount_eur)}
          </span>
        </div>
      )}
    </div>
  );
}
