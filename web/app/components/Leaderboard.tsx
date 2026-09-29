import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import type { Player } from "@/lib/api";

const BAR_COLOR = "#2a78d6";

export function Leaderboard({
  title,
  players,
  metricKey,
  limit = 8,
}: {
  title: string;
  players: Player[];
  metricKey: keyof Player;
  limit?: number;
}) {
  const ranked = [...players]
    .filter((player) => Number(player[metricKey]) > 0)
    .sort((a, b) => Number(b[metricKey]) - Number(a[metricKey]))
    .slice(0, limit);

  if (ranked.length === 0) {
    return null;
  }

  const max = Math.max(...ranked.map((player) => Number(player[metricKey])));

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      <div className="flex flex-col gap-2 rounded-md border border-zinc-200 p-4 dark:border-zinc-800">
        {ranked.map((player, index) => {
          const value = Number(player[metricKey]);
          return (
            <Link
              key={player.player_id}
              href={`/players/${player.player_id}`}
              className="group flex items-center gap-3"
            >
              <span className="w-4 shrink-0 text-right text-xs text-zinc-400">
                {index + 1}
              </span>
              <Avatar name={player.name} photoUrl={player.photo_url} size={28} />
              <span className="w-28 shrink-0 truncate text-sm font-medium group-hover:underline sm:w-40">
                {player.name}
              </span>
              <div className="h-3 flex-1 rounded-full bg-zinc-100 dark:bg-zinc-800">
                <div
                  className="h-3 rounded-full"
                  style={{
                    width: `${(value / max) * 100}%`,
                    backgroundColor: BAR_COLOR,
                  }}
                />
              </div>
              <span className="w-10 shrink-0 text-right text-sm font-medium tabular-nums">
                {value}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
