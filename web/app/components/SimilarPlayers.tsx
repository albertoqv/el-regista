import Link from "next/link";
import { Reveal } from "@/app/components/Reveal";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import type { TwinReport } from "@/lib/api";
import { competitionColor, formatMarketValue, seasonDisplay } from "@/lib/format";
import { saving } from "@/lib/twins";

/** Compact twin strip for the player page; the full tool lives in /gemelos. */
export function SimilarPlayers({ report }: { report: TwinReport | null }) {
  if (!report || report.twins.length === 0) {
    return (
      <p className="glass rounded-lg p-6 text-sm text-muted">
        Aún no hay suficientes jugadores comparables.
      </p>
    );
  }
  const { target, twins } = report;

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      {twins.map((twin, index) => {
        const value = saving(target, twin);
        return (
          <Reveal key={twin.player_id} delay={index * 0.05}>
            <Link
              href={`/compare?${new URLSearchParams({
                a: String(target.player_id),
                b: String(twin.player_id),
                sac: target.competition,
                sal: target.season_label,
                sbc: twin.competition,
                sbl: twin.season_label,
              }).toString()}`}
              className="group relative block"
            >
              <PlayerPortrait
                name={twin.name}
                photoUrl={twin.photo_url}
                accent={competitionColor(twin.competition)}
                rounded="rounded-lg"
                className="aspect-[3/4] transition duration-500 group-hover:-translate-y-1"
              />
              <span className="absolute right-2 top-2 rounded-full bg-black/65 px-2 py-0.5 font-heading text-sm text-on-photo">
                {twin.similarity}%
              </span>
              <div className="absolute inset-x-0 bottom-0 p-3">
                <span className="block truncate text-sm font-semibold">{twin.name}</span>
                <span className="block truncate text-xs text-muted">
                  {twin.team ?? twin.competition} {seasonDisplay(twin.season_label)}
                </span>
                {twin.role_match === "same" || twin.role_match === "similar" ? (
                  <span className="block truncate text-xs text-muted">
                    {twin.role_match === "same" ? "Mismo rol" : "Rol parecido"}
                  </span>
                ) : null}
                {twin.market_value_eur !== null && (
                  <span
                    className={`mt-1 inline-block rounded-md px-1.5 py-0.5 text-xs font-bold ${value.kind === "cheaper" ? "bg-grass/15 text-brand-2" : "bg-ink/10 text-ink/80"}`}
                  >
                    {formatMarketValue(twin.market_value_eur)}
                    {value.kind === "cheaper" && ` · −${value.share}%`}
                  </span>
                )}
              </div>
            </Link>
          </Reveal>
        );
      })}
    </div>
  );
}
