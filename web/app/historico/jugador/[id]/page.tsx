import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { PeakCard } from "@/app/components/PeakCard";
import { PercentileLegend } from "@/app/components/PercentileBars";
import { RadarChart } from "@/app/components/RadarChart";
import { Reveal } from "@/app/components/Reveal";
import { competitionColor, seasonDisplay } from "@/lib/format";
import { HISTORY_METRICS } from "@/lib/history";
import {
  bestSeason,
  closestAcrossEras,
  LINE_LABELS,
  loadProfiles,
  pickValue,
  seasonKey,
  seasonName,
  seasonScore,
  seasonsOf,
} from "@/lib/profiles";

type Props = PageProps<"/historico/jugador/[id]">;

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { id } = await props.params;
  const seasons = seasonsOf(Number(id), await loadProfiles());
  const last = seasons[seasons.length - 1];
  if (!last) return { title: "El Regista" };
  return {
    title: `${last.name}: sus temporadas desde 2014 · El Regista`,
    description: `Radar, mejor temporada y gemelos de época de ${last.name} en las 5 grandes ligas, con datos de Understat.`,
  };
}

/** A player of the big five since 2014 that the database does not have (retired,
 * or abroad now): every regular season from the static history. */
export default async function HistoryPlayerPage(props: Props) {
  const { id } = await props.params;
  const profiles = await loadProfiles();
  const seasons = seasonsOf(Number(id), profiles);
  if (seasons.length === 0) notFound();
  const last = seasons[seasons.length - 1];
  const best = bestSeason(seasons) ?? last;
  const accent = competitionColor(best.competition);
  const closest = closestAcrossEras(seasons, profiles);
  const teams = [...new Set(seasons.map((season) => season.team))];

  return (
    <div className="flex flex-col gap-10">
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-5xl leading-[0.92] sm:text-6xl">{last.name}</h1>
        <p className="text-sm text-muted sm:text-base">
          {LINE_LABELS[last.line].slice(0, -1).toLowerCase()} · {teams.join(", ")} · {seasonDisplay(String(seasons[0].year))}
          {seasons.length > 1 ? ` a ${seasonDisplay(String(last.year))}` : ""} en las 5 grandes
        </p>
        <nav className="mt-2 flex flex-wrap gap-2">
          <Link href={`/epocas?j=${best.id}&s=${seasonKey(best)}`} className="glass glass-hover rounded-lg px-4 py-2 text-sm font-semibold">
            Gemelos de época
          </Link>
          <Link href={`/epocas/duelo?a=${pickValue(best)}`} className="glass glass-hover rounded-lg px-4 py-2 text-sm font-semibold">
            Cara a cara
          </Link>
        </nav>
      </header>

      {closest && (
        <Reveal>
          <Link
            href={`/epocas/duelo?a=${pickValue(closest.season)}&b=${pickValue(closest.profile)}`}
            className="glass glass-hover flex flex-wrap items-baseline justify-between gap-3 rounded-lg p-5"
          >
            <span className="text-lg">
              Su {seasonDisplay(String(closest.season.year))} se parece al{" "}
              <strong>
                {closest.profile.name} de la {seasonDisplay(String(closest.profile.year))}
              </strong>
            </span>
            <span className="font-display text-3xl tabular-nums">{closest.similarity}%</span>
          </Link>
        </Reveal>
      )}

      {seasons.length >= 2 ? (
        <Reveal>
          <PeakCard seasons={seasons} color={accent} />
        </Reveal>
      ) : (
        <Reveal>
          <section className="glass rounded-lg p-6">
            <h2 className="font-heading text-2xl tracking-tight">{seasonName(last)}</h2>
            <RadarChart axes={HISTORY_METRICS} series={[{ name: last.name, color: accent, values: last.percentiles }]} />
            <PercentileLegend />
          </section>
        </Reveal>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-2xl tracking-tight">Temporada a temporada</h2>
        <div className="-mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
          <table className="w-full min-w-[640px] text-sm">
            <thead className="text-left text-muted">
              <tr className="border-b border-line">
                <th className="py-2 font-semibold">Temporada</th>
                <th className="py-2 font-semibold">Equipo</th>
                <th className="py-2 text-right font-semibold">Min.</th>
                <th className="py-2 text-right font-semibold">Goles</th>
                <th className="py-2 text-right font-semibold">xG</th>
                <th className="py-2 text-right font-semibold">Asist.</th>
                <th className="py-2 text-right font-semibold">xA</th>
                <th className="py-2 text-right font-semibold">Nota</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {[...seasons].reverse().map((season) => (
                <tr key={seasonKey(season)}>
                  <td className="py-2.5">
                    <Link href={`/epocas?j=${season.id}&s=${seasonKey(season)}`} className="font-semibold hover:underline">
                      {seasonName(season)}
                    </Link>
                  </td>
                  <td className="py-2.5">{season.team}</td>
                  <td className="py-2.5 text-right tabular-nums">{season.minutes.toLocaleString("es-ES")}</td>
                  <td className="py-2.5 text-right tabular-nums">{season.totals.goals}</td>
                  <td className="py-2.5 text-right tabular-nums">{season.totals.expected_goals.toFixed(1)}</td>
                  <td className="py-2.5 text-right tabular-nums">{season.totals.assists}</td>
                  <td className="py-2.5 text-right tabular-nums">{season.totals.expected_assists.toFixed(1)}</td>
                  <td className="py-2.5 text-right font-semibold tabular-nums" style={season === best ? { color: accent } : undefined}>
                    {seasonScore(season)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-muted">
          Solo temporadas de liga de 900 minutos o más en LaLiga, Premier, Serie A, Bundesliga y Ligue 1, con datos de Understat.
        </p>
      </section>
    </div>
  );
}
