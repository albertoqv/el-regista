import Link from "next/link";
import { RadarChart } from "@/app/components/RadarChart";
import { seasonDisplay } from "@/lib/format";
import { HISTORY_METRICS } from "@/lib/history";
import { bestSeason, seasonKey, seasonScore, type Profile } from "@/lib/profiles";

// Within this many points of his best, he is still at his peak.
const PEAK_MARGIN = 5;

/** His best season by Understat's percentiles against his latest one, and every
 * season's mark in between. */
export function PeakCard({ seasons, color }: { seasons: Profile[]; color: string }) {
  const best = bestSeason(seasons);
  if (!best || seasons.length < 2) return null;
  const latest = seasons[seasons.length - 1];
  const gap = seasonScore(best) - seasonScore(latest);
  const name = (profile: Profile) => `${profile.competition} ${seasonDisplay(String(profile.year))}`;

  return (
    <section className="glass grid grid-cols-1 gap-8 rounded-lg p-6 lg:grid-cols-2">
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="font-heading text-2xl tracking-tight">Su mejor temporada</h2>
          <p className="text-sm text-muted">
            Nota = media de sus percentiles de Understat frente a los de su puesto, liga y temporada (900 minutos o más).
          </p>
        </div>
        <p className="text-lg">
          <Link href={`/epocas?j=${best.id}&s=${seasonKey(best)}`} className="font-semibold hover:underline" style={{ color }}>
            {name(best)}
          </Link>{" "}
          con el {best.team}: <span className="font-display text-3xl tabular-nums">{seasonScore(best)}</span>.{" "}
          {best === latest
            ? "Es la última: está en su mejor momento."
            : gap <= PEAK_MARGIN
              ? `La última (${name(latest)}, ${seasonScore(latest)}) sigue a su altura.`
              : `La última (${name(latest)}) se queda en ${seasonScore(latest)}, ${gap} puntos por debajo.`}
        </p>
        <ol className="flex gap-1" aria-label="Nota de cada temporada">
          {seasons.map((season) => (
            <li key={seasonKey(season)} className="flex flex-1 flex-col items-center gap-1">
              <span className="text-xs tabular-nums text-muted">{seasonScore(season)}</span>
              {/* Fixed height: a percentage height needs a parent with a definite one. */}
              <span className="flex h-24 w-full items-end">
                <Link
                  href={`/epocas?j=${season.id}&s=${seasonKey(season)}`}
                  title={`${name(season)} · ${season.team}: ${seasonScore(season)}`}
                  className="w-full rounded-t"
                  style={{
                    height: `${Math.max(seasonScore(season), 4)}%`,
                    background: season === best ? color : "rgba(22,23,27,0.18)",
                  }}
                />
              </span>
              <span className="text-xs tabular-nums text-muted">{String(season.year).slice(2)}</span>
            </li>
          ))}
        </ol>
        <Link href={`/epocas?j=${best.id}&s=${seasonKey(best)}`} className="w-fit font-semibold text-brand hover:underline">
          Quién juega hoy como él en su mejor año →
        </Link>
      </div>
      <div className="flex flex-col gap-2">
        <RadarChart
          axes={HISTORY_METRICS}
          series={[
            { name: `Mejor: ${seasonDisplay(String(best.year))}`, color, values: best.percentiles },
            ...(best === latest
              ? []
              : [{ name: `Última: ${seasonDisplay(String(latest.year))}`, color: "#16171b", values: latest.percentiles }]),
          ]}
        />
        {best !== latest && (
          <p className="flex justify-center gap-5 text-sm">
            <span className="font-semibold" style={{ color }}>Mejor: {name(best)}</span>
            <span className="font-semibold">Última: {name(latest)}</span>
          </p>
        )}
      </div>
    </section>
  );
}
