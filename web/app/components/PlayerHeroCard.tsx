import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import type { MarketValuePoint, Player } from "@/lib/api";
import { footLabel, formatAge, formatMarketValue } from "@/lib/format";

function Chip({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-center rounded-md border border-zinc-200 px-3 py-1.5 dark:border-zinc-800">
      <span className="text-[10px] uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        {label}
      </span>
      <span className="text-sm font-semibold">{value}</span>
    </div>
  );
}

export function PlayerHeroCard({
  player,
  seasonLabel,
  currentMarketValue,
}: {
  player: Player;
  seasonLabel: string;
  currentMarketValue: MarketValuePoint | null;
}) {
  const age = formatAge(player);

  return (
    <Link
      href={`/players/${player.player_id}`}
      className="flex flex-1 flex-col items-center gap-3 text-center hover:opacity-90"
    >
      <Avatar name={player.name} photoUrl={player.photo_url} size={140} />
      <div>
        <p className="text-xl font-semibold">{player.name}</p>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          {player.position} · {seasonLabel}
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {age && <Chip label="Edad" value={age} />}
        {player.preferred_foot && (
          <Chip label="Pie" value={footLabel(player.preferred_foot)} />
        )}
        {currentMarketValue && (
          <Chip
            label="Valor"
            value={formatMarketValue(currentMarketValue.amount_eur)}
          />
        )}
      </div>
    </Link>
  );
}
