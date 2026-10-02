import type { Metadata } from "next";
import Link from "next/link";
import { listSeasonLeaders, type SeasonLeader } from "@/lib/api";
import { currentSeasonStartYear, seasonDisplay } from "@/lib/format";
import { RANKING_LEAGUES, RANKING_METRICS, rankingHref } from "@/lib/rankings";

const season = () => seasonDisplay(String(currentSeasonStartYear()));

export function generateMetadata(): Metadata {
  return {
    title: `Rankings ${season()}: goleadores, asistentes y xG · El Regista`,
    description: "Goleadores, asistentes, xG, xA, tiros y pases clave de LaLiga, Premier, Serie A, Bundesliga y Ligue 1.",
    alternates: { canonical: "/ranking" },
  };
}

export default async function RankingIndexPage() {
  const scorers = await Promise.all(
    RANKING_LEAGUES.map((league) =>
      listSeasonLeaders(currentSeasonStartYear(), { metric: "goals", competition: league.competition, limit: 3 }).catch(
        (): SeasonLeader[] => [],
      ),
    ),
  );

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-5xl leading-[0.92] sm:text-6xl">Rankings {season()}</h1>
        <p className="text-sm text-muted">Las cinco grandes ligas, actualizadas martes y viernes.</p>
      </header>

      <div className="grid grid-cols-1 gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
        {RANKING_LEAGUES.map((league, index) => (
          <section key={league.slug} className="flex flex-col gap-3 border-t-2 border-ink pt-3">
            <h2 className="font-heading text-2xl tracking-tight">
              <Link href={rankingHref(league.slug, "goleadores")} className="hover:text-brand">
                {league.competition}
              </Link>
            </h2>
            <ol className="flex flex-col gap-1">
              {scorers[index].map((leader, rank) => (
                <li key={leader.player_id} className="flex items-baseline gap-2">
                  <span className="w-4 text-sm text-muted tabular-nums">{rank + 1}</span>
                  <Link href={`/players/${leader.player_id}`} className="min-w-0 flex-1 truncate font-semibold hover:text-brand">
                    {leader.name}
                  </Link>
                  <span className="font-display text-xl tabular-nums">{leader.goals}</span>
                </li>
              ))}
            </ol>
            <nav className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
              {RANKING_METRICS.map((metric) => (
                <Link key={metric.slug} href={rankingHref(league.slug, metric.slug)} className="hover:text-ink">
                  {metric.label}
                </Link>
              ))}
            </nav>
          </section>
        ))}
      </div>
    </div>
  );
}
