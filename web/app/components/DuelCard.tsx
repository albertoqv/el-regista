import Link from "next/link";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import type { SeasonLeader } from "@/lib/api";

function compareHref(a: SeasonLeader, b: SeasonLeader): string {
  const params = new URLSearchParams({
    a: String(a.player_id),
    b: String(b.player_id),
    sac: a.competition,
    sal: a.season_label,
    sbc: b.competition,
    sbl: b.season_label,
  });
  return `/compare?${params.toString()}`;
}

export function DuelCard({
  title,
  a,
  b,
}: {
  title: string;
  a: SeasonLeader;
  b: SeasonLeader;
}) {
  return (
    <Link
      href={compareHref(a, b)}
      className="glass glass-hover group relative flex flex-col gap-4 overflow-hidden rounded-lg p-4"
    >
      <span className="text-xs font-semibold text-muted">
        {title}
      </span>
      <div className="relative grid grid-cols-2 gap-2">
        <PlayerPortrait
          name={a.name}
          photoUrl={a.photo_url}
          accent="#9ccfea"
          rounded="rounded-lg"
          className="aspect-[4/5] transition duration-500 group-hover:-translate-x-1"
        />
        <PlayerPortrait
          name={b.name}
          photoUrl={b.photo_url}
          accent="#f28c6b"
          mirrored
          rounded="rounded-lg"
          className="aspect-[4/5] transition duration-500 group-hover:translate-x-1"
        />
        <span className="absolute left-1/2 top-1/2 flex h-12 w-12 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/20 bg-[#1d0e14] font-display text-sm font-bold italic transition duration-500 group-hover:scale-110">
          VS
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <span className="truncate font-semibold text-side-a">{a.name}</span>
        <span className="truncate text-right font-semibold text-side-b">{b.name}</span>
      </div>
    </Link>
  );
}
