import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Avatar } from "@/app/components/Avatar";
import { JsonLd } from "@/app/components/JsonLd";
import { listSeasonLeaders, type SeasonLeader } from "@/lib/api";
import { currentSeasonStartYear, positionShort, seasonDisplay } from "@/lib/format";
import { METRICS } from "@/lib/metrics";
import { findRanking, metricsFor, RANKING_LEAGUES, rankingHref, rankingPages } from "@/lib/rankings";
import { SITE_URL } from "@/lib/site";

const LIMIT = 50;
const LEAGUE_GROUPS = [
  { label: "5 grandes", leagues: RANKING_LEAGUES.filter((league) => !league.basic) },
  { label: "Otras ligas", leagues: RANKING_LEAGUES.filter((league) => league.basic) },
];
// Below three full matches the per-90 rate is noise (2 goals in 29' = 6.21).
const MIN_MINUTES_PER_90 = 270;

export const dynamicParams = false;

export function generateStaticParams() {
  return rankingPages().map(({ league, metric }) => ({ liga: league.slug, metrica: metric.slug }));
}

function headline(liga: string, metrica: string, season = currentSeasonStartYear()): string {
  const ranking = findRanking(liga, metrica);
  if (!ranking) return "Ranking";
  return `${ranking.metric.title} de ${ranking.league.name} ${seasonDisplay(String(season))}`;
}

export async function generateMetadata(props: PageProps<"/ranking/[liga]/[metrica]">): Promise<Metadata> {
  const { liga, metrica } = await props.params;
  const ranking = findRanking(liga, metrica);
  if (!ranking) return {};
  return {
    title: `${headline(liga, metrica)} · El Regista`,
    description: `Clasificación de ${ranking.metric.unit} de ${ranking.league.name} esta temporada, con minutos y ritmo por 90'. Se actualiza martes y viernes.`,
    alternates: { canonical: rankingHref(liga, metrica) },
  };
}

function per90(value: number, minutes: number): string {
  return minutes >= MIN_MINUTES_PER_90 ? ((value / minutes) * 90).toFixed(2) : "–";
}

export default async function RankingPage(props: PageProps<"/ranking/[liga]/[metrica]">) {
  const { liga, metrica } = await props.params;
  const ranking = findRanking(liga, metrica);
  if (!ranking) notFound();
  const { league, metric } = ranking;
  const load = (year: number) =>
    listSeasonLeaders(year, { metric: metric.metric, competition: league.competition, limit: LIMIT }).catch(
      (): SeasonLeader[] => [],
    );
  // Before the new season's first data arrives, the last finished one (named in the title).
  let season = currentSeasonStartYear();
  let leaders = await load(season);
  if (leaders.length === 0) {
    const previous = await load(season - 1);
    if (previous.length > 0) {
      season -= 1;
      leaders = previous;
    }
  }
  const decimals = METRICS[metric.metric].decimals ?? 0;
  const title = headline(liga, metrica, season);

  return (
    <div className="flex flex-col gap-8">
      <JsonLd
        data={{
          "@type": "ItemList",
          name: title,
          itemListOrder: "https://schema.org/ItemListOrderDescending",
          numberOfItems: leaders.length,
          itemListElement: leaders.map((leader, index) => ({
            "@type": "ListItem",
            position: index + 1,
            url: `${SITE_URL}/players/${leader.player_id}`,
            name: leader.name,
          })),
        }}
      />
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-5xl leading-[0.92] sm:text-6xl">{title}</h1>
        <p className="text-sm text-muted">
          {METRICS[metric.metric].help} Datos de {league.basic ? "Transfermarkt" : "FBref y Understat"}, se actualizan martes y viernes.
        </p>
      </header>

      <nav aria-label="Métrica" className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
        {metricsFor(league).map((entry) => (
          <Link
            key={entry.slug}
            href={rankingHref(liga, entry.slug)}
            aria-current={entry.slug === metrica ? "page" : undefined}
            className={`shrink-0 rounded-lg px-4 py-2 text-sm font-semibold transition ${entry.slug === metrica ? "bg-ink text-bg" : "glass glass-hover"}`}
          >
            {entry.label}
          </Link>
        ))}
      </nav>
      <div className="-mt-4 flex flex-col gap-2">
        {LEAGUE_GROUPS.map((group) => (
          <nav key={group.label} aria-label={group.label} className="flex items-center gap-2">
            <span className="w-24 shrink-0 text-sm font-semibold text-muted">{group.label}</span>
            <div className="no-scrollbar -mr-4 flex gap-1.5 overflow-x-auto pr-4 sm:mr-0 sm:flex-wrap sm:pr-0">
              {group.leagues.map((entry) => {
                // Extra leagues only have goals and assists: other metrics open their scorers.
                const target = metricsFor(entry).some((m) => m.slug === metrica) ? metrica : "goleadores";
                return (
                  <Link
                    key={entry.slug}
                    href={rankingHref(entry.slug, target)}
                    aria-current={entry.slug === liga ? "page" : undefined}
                    className={`shrink-0 rounded-full px-3 py-1.5 text-sm font-medium ${entry.slug === liga ? "bg-ink text-bg" : "text-muted hover:bg-ink/5 hover:text-ink"}`}
                  >
                    {entry.competition}
                  </Link>
                );
              })}
            </div>
          </nav>
        ))}
      </div>

      {leaders.length === 0 ? (
        <p className="glass rounded-lg p-8 text-center text-sm text-muted">Todavía no hay datos de esta temporada.</p>
      ) : (
        <ol className="flex flex-col divide-y divide-line border-y border-line">
          {leaders.map((leader, index) => {
            const value = leader[metric.metric];
            return (
              <li key={leader.player_id}>
                <Link
                  href={`/players/${leader.player_id}`}
                  className="flex items-center gap-3 px-1 py-3 transition hover:bg-ink/5 sm:gap-4 sm:px-3"
                >
                  <span className="w-7 shrink-0 text-right font-heading text-base tabular-nums text-muted">{index + 1}</span>
                  <Avatar name={leader.name} photoUrl={leader.photo_url} size={40} />
                  <span className="flex min-w-0 flex-1 flex-col">
                    <span className="truncate font-semibold">{leader.name}</span>
                    <span className="truncate text-xs text-muted">
                      {leader.team ?? league.competition} · {positionShort(leader.position)} · {leader.minutes_played}&apos;
                    </span>
                  </span>
                  <span className="hidden w-20 shrink-0 text-right text-xs text-muted sm:block">
                    {per90(value, leader.minutes_played)} por 90&apos;
                  </span>
                  <span className="w-14 shrink-0 text-right font-display text-3xl tabular-nums">
                    {value.toFixed(decimals)}
                  </span>
                </Link>
              </li>
            );
          })}
        </ol>
      )}

      <p className="text-sm text-muted">
        Otras ligas y filtros por edad, puesto o precio en el{" "}
        <Link href="/explorar" className="font-semibold text-ink underline decoration-line underline-offset-4 hover:text-brand">
          explorador
        </Link>
        .
      </p>
    </div>
  );
}
