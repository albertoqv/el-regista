import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { Reveal } from "@/app/components/motion";
import { HandArrow, ScoutNote } from "@/app/components/ScoutNote";
import type { Partnership } from "@/lib/api";

/** Who feeds whom: assister → scorer pairs with the most goals together. */
export function Partnerships({ pairs }: { pairs: Partnership[] }) {
  if (pairs.length === 0) return null;
  return (
    <section className="flex flex-col gap-5">
      <div>
        <ScoutNote rotate={-3}>se entienden solos</ScoutNote>
        <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
          Las parejas que más goles fabrican
        </h2>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {pairs.map((pair, index) => (
          <Reveal key={`${pair.scorer.player_id}-${pair.assister_name}`} delay={index * 0.05}>
            <div
              className="glass glass-hover flex items-center gap-3 rounded-lg p-4"
              style={{ transform: `rotate(${index % 2 === 0 ? -0.6 : 0.6}deg)` }}
            >
              <div className="flex flex-col items-center gap-1">
                {pair.assister ? (
                  <Link href={`/players/${pair.assister.player_id}`}>
                    <Avatar name={pair.assister_name} photoUrl={pair.assister.photo_url} size={52} />
                  </Link>
                ) : (
                  <Avatar name={pair.assister_name} size={52} />
                )}
              </div>
              <HandArrow direction="right" className="shrink-0 text-[#9ccfea]" />
              <Link href={`/players/${pair.scorer.player_id}`}>
                <Avatar name={pair.scorer.name} photoUrl={pair.scorer.photo_url} size={52} />
              </Link>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold">
                  {pair.assister_name.split(" ").slice(-1)[0]} → {pair.scorer.name.split(" ").slice(-1)[0]}
                </p>
                <p className="flex items-center gap-1.5 truncate text-xs text-muted">
                  {pair.team}
                </p>
              </div>
              <div className="text-right">
                <span className="block font-display text-3xl font-bold leading-none">{pair.goals}</span>
                <span className="text-xs text-muted">goles</span>
              </div>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
