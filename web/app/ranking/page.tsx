import type { Metadata } from "next";
import Link from "next/link";
import { listSeasonLeaders, type SeasonLeader } from "@/lib/api";
import { currentSeasonStartYear, seasonDisplay } from "@/lib/format";
import { RANKING_LEAGUES, RANKING_METRICS, rankingHref } from "@/lib/rankings";

const BIG_FIVE = RANKING_LEAGUES.filter((league) => !league.basic);
const BASIC_GROUPS = [
  { title: "Otras ligas", leagues: RANKING_LEAGUES.filter((league) => league.basic && !league.second) },
  { title: "Segundas divisiones", leagues: RANKING_LEAGUES.filter((league) => league.second) },
];

const season = () => seasonDisplay(String(currentSeasonStartYear()));

export function generateMetadata(): Metadata {
  return {
    title: `Rankings ${season()}: goleadores, asistentes y xG · El Regista`,
    description: "Goleadores, asistentes, xG, xA, tiros y pases clave de las 5 grandes, y goleadores y asistentes de 28 ligas más, segundas divisiones incluidas.",
    alternates: { canonical: "/ranking" },
  };
}

export default async function RankingIndexPage() {
  const scorers = await Promise.all(
    BIG_FIVE.map((league) =>
      listSeasonLeaders(currentSeasonStartYear(), { metric: "goals", competition: league.competition, limit: 3 }).catch(
        (): SeasonLeader[] => [],
      ),
    ),
  );

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-5xl leading-[0.92] sm:text-6xl">Rankings {season()}</h1>
        <p className="text-sm text-muted">33 ligas, actualizadas martes y viernes.</p>
      </header>

      <div className="grid grid-cols-1 gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
        {BIG_FIVE.map((league, index) => (
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

      {BASIC_GROUPS.map((group) => (
        <section key={group.title} className="flex flex-col gap-3 border-t-2 border-ink pt-3">
          <h2 className="font-heading text-2xl tracking-tight">{group.title}</h2>
          <p className="text-sm text-muted">Solo goles y asistencias.</p>
          <ul className="grid grid-cols-1 gap-x-8 gap-y-2 sm:grid-cols-2 lg:grid-cols-3">
            {group.leagues.map((league) => (
              <li key={league.slug} className="flex items-baseline justify-between gap-3 border-b border-line py-2">
                <Link href={rankingHref(league.slug, "goleadores")} className="min-w-0 truncate font-semibold hover:text-brand">
                  {league.competition}
                </Link>
                <span className="flex shrink-0 gap-3 text-sm text-muted">
                  <Link href={rankingHref(league.slug, "goleadores")} className="hover:text-ink">
                    Goles
                  </Link>
                  <Link href={rankingHref(league.slug, "asistentes")} className="hover:text-ink">
                    Asistencias
                  </Link>
                </span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
