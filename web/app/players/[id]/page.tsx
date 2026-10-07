import { preconnect } from "react-dom";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CareerChart } from "@/app/components/CareerChart";
import { CompetitionStats } from "@/app/components/CompetitionStats";
import { MarketValueChart } from "@/app/components/MarketValueChart";
import { SITE_URL } from "@/lib/site";
import { JsonLd } from "@/app/components/JsonLd";
import { Reveal } from "@/app/components/Reveal";
import { TrendChart } from "@/app/components/TrendChart";
import { CountUp } from "@/app/components/motion";
import { PercentileBars, PercentileLegend } from "@/app/components/PercentileBars";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { PlayerStats } from "@/app/components/PlayerStats";
import { RadarChart } from "@/app/components/RadarChart";
import { SeasonSelector } from "@/app/components/SeasonSelector";
import { ShareCard } from "@/app/components/ShareCard";
import { ShotProfile } from "@/app/components/ShotProfile";
import { SimilarPlayers } from "@/app/components/SimilarPlayers";
import {
  ApiError,
  type CareerCurve,
  type CompetitionLine,
  findTwins,
  getMarketValue,
  getPlayerCareer,
  getPlayerCompetitions,
  getPlayer,
  getPlayerPercentiles,
  getPlayerShots,
  getPlayerTrend,
  getPlayerSeason,
  listPlayerSeasons,
  type MarketValueHistory,
  type PercentileReport,
  type PlayerShot,
  type PlayerTrend,
  type Season,
  type TwinReport,
} from "@/lib/api";
import {
  competitionColor,
  footLabel,
  formatAge,
  formatMarketValue,
  positionLabel,
  roleLabel,
  seasonDisplay,
  sortSeasonsByRecency,
} from "@/lib/format";
import { RADAR_METRICS } from "@/lib/metrics";
import { resolveSeason } from "@/lib/seasons";

function param(value: string | string[] | undefined): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function Badge({ label, value }: { label: string; value: string }) {
  return (
    <div className="glass flex flex-col rounded-lg px-4 py-2.5">
      <span className="text-xs font-semibold text-muted">
        {label}
      </span>
      <span className="font-heading text-base">{value}</span>
    </div>
  );
}

export async function generateMetadata(
  props: PageProps<"/players/[id]">,
): Promise<Metadata> {
  const { id } = await props.params;
  const player = await getPlayer(Number(id)).catch(() => null);
  if (!player) return { title: "El Regista" };
  return {
    title: `${player.name} · El Regista`,
    description: `Perfil de scouting, gemelos y estadísticas de ${player.name}.`,
    alternates: { canonical: `/players/${id}` },
    openGraph: { images: [`/players/${id}/card`] },
    twitter: { card: "summary_large_image", images: [`/players/${id}/card`] },
  };
}

export default async function PlayerDetailPage(props: PageProps<"/players/[id]">) {
  // Player photos come from Transfermarkt: open the connection before the HTML needs it.
  preconnect("https://img.a.transfermarkt.technology");
  const { id } = await props.params;
  const playerId = Number(id);
  const searchParams = await props.searchParams;

  const seasons = sortSeasonsByRecency(
    await listPlayerSeasons(playerId).catch((error: unknown) => {
      if (error instanceof ApiError && error.status === 404) notFound();
      return [] as Season[];
    }),
  );
  const season = resolveSeason(seasons, param(searchParams.sc), param(searchParams.sl));

  let player;
  try {
    player = season ? await getPlayerSeason(playerId, season) : await getPlayer(playerId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const [twins, marketValue, percentiles, shots, trend, competitions, career] = await Promise.all([
    findTwins(playerId, { limit: 6 }).catch((): TwinReport | null => null),
    getMarketValue(playerId).catch(
      (): MarketValueHistory => ({ current: null, history: [] }),
    ),
    season
      ? getPlayerPercentiles(playerId, season).catch(() => null)
      : Promise.resolve<PercentileReport | null>(null),
    getPlayerShots(playerId, season?.label).catch((): PlayerShot[] => []),
    getPlayerTrend(playerId).catch((): PlayerTrend | null => null),
    getPlayerCompetitions(playerId).catch((): CompetitionLine[] => []),
    getPlayerCareer(playerId).catch((): CareerCurve | null => null),
  ]);

  const age = formatAge(player);
  const team = season ? seasons.find((s) => s.label === season.label && s.competition === season.competition)?.team : null;
  const accent = season ? competitionColor(season.competition) : "#c93c17";
  const contributions = player.goals + player.assists;

  return (
    <div className="flex flex-col gap-14">
      <JsonLd
        data={{
          "@type": "Person",
          name: player.name,
          url: `${SITE_URL}/players/${playerId}`,
          jobTitle: "Futbolista",
          ...(player.date_of_birth ? { birthDate: player.date_of_birth } : {}),
          ...(player.photo_url ? { image: player.photo_url } : {}),
          ...(player.height_cm ? { height: `${player.height_cm} cm` } : {}),
          ...(seasons[0]?.team ? { memberOf: { "@type": "SportsTeam", name: seasons[0].team } } : {}),
        }}
      />
      <section className="relative">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-6 left-0 right-0 select-none overflow-hidden whitespace-nowrap text-center font-display text-[18vw] font-bold uppercase leading-none text-ink/[0.03] sm:text-[9rem]"
        >
          {player.name.split(" ").slice(-1)[0]}
        </div>

        <div className="relative grid grid-cols-1 items-end gap-8 md:grid-cols-[320px_1fr]">
          <Reveal>
            <PlayerPortrait
              name={player.name}
              photoUrl={player.photo_url}
              accent={accent}
              className="mx-auto aspect-[3/4] w-full max-w-[320px]"
              priority
            />
          </Reveal>

          <div className="flex flex-col gap-5">
            <Reveal delay={0.05}>
              <p className="flex items-center gap-2 text-sm font-semibold text-muted">
                {roleLabel(player)}
                {team && <span className="text-muted">· {team}</span>}
              </p>
              <h1 className="font-display text-5xl font-bold leading-none tracking-tight sm:text-6xl">
                {player.name}
              </h1>
            </Reveal>

            <Reveal delay={0.1} className="flex flex-wrap gap-2">
              {age && <Badge label="Edad" value={`${age} años`} />}
              {player.preferred_foot && <Badge label="Pie" value={footLabel(player.preferred_foot)} />}
              {player.height_cm && <Badge label="Altura" value={`${player.height_cm} cm`} />}
              {marketValue.current && (
                <Badge label="Valor" value={formatMarketValue(marketValue.current.amount_eur)} />
              )}
              <Badge
                label={season ? `${season.competition} ${seasonDisplay(season.label)}` : "Carrera"}
                value={`${player.minutes_played.toLocaleString("es-ES")} min`}
              />
            </Reveal>

            <Reveal delay={0.15} className="grid grid-cols-3 gap-3">
              {[
                { label: "Goles", value: player.goals, decimals: 0 },
                { label: "Asistencias", value: player.assists, decimals: 0 },
                { label: "Goles + asist.", value: contributions, decimals: 0 },
              ].map((stat) => (
                <div key={stat.label} className="glass rounded-lg p-4">
                  <span className="block font-display text-4xl font-bold tabular-nums sm:text-5xl">
                    <CountUp value={stat.value} decimals={stat.decimals} />
                  </span>
                  <span className="text-xs text-muted">{stat.label}</span>
                </div>
              ))}
            </Reveal>

            <Reveal delay={0.2} className="flex flex-wrap gap-3">
              <Link
                href={`/compare?a=${player.player_id}${season ? `&sac=${encodeURIComponent(season.competition)}&sal=${encodeURIComponent(season.label)}` : ""}`}
                className="rounded-full bg-brand px-5 py-2.5 text-sm font-semibold text-bg transition hover:brightness-110"
              >
                Comparar con otro jugador
              </Link>
              <ShareCard playerId={player.player_id} name={player.name} />
              <a
                href="#parecidos"
                className="glass rounded-full px-5 py-2.5 text-sm font-semibold transition hover:border-line-strong"
              >
                Ver sus gemelos
              </a>
            </Reveal>
          </div>
        </div>
      </section>

      {seasons.length > 0 && (
        <SeasonSelector playerId={playerId} seasons={seasons} selected={season} />
      )}

      {percentiles && (
        <Reveal>
          <section className="glass grid grid-cols-1 gap-8 rounded-lg p-6 lg:grid-cols-2">
            <div className="flex flex-col gap-3">
              <div>
                <h2 className="font-heading text-2xl tracking-tight">
                  Perfil de scouting
                </h2>
                <p className="text-sm text-muted">
                  Percentil frente a {percentiles.peer_count} {positionLabel(percentiles.position).toLowerCase()}s
                  de {percentiles.competition} {seasonDisplay(percentiles.season_label)} con al menos{" "}
                  {percentiles.minimum_minutes} minutos. 90 = mejor que el 90% de ellos.
                </p>
              </div>
              <RadarChart
                axes={RADAR_METRICS}
                series={[
                  {
                    name: player.name,
                    color: accent,
                    values: Object.fromEntries(
                      Object.entries(percentiles.metrics).map(([key, value]) => [key, value.percentile]),
                    ),
                  },
                ]}
              />
              <PercentileLegend />
            </div>
            <PercentileBars report={percentiles} />
          </section>
        </Reveal>
      )}

      {shots.length > 0 && (
        <Reveal>
          <ShotProfile shots={shots} color={accent} />
        </Reveal>
      )}

      {marketValue.history.length > 0 && (
        <Reveal>
          <MarketValueChart series={[{ name: player.name, color: "#1f8a4c", history: marketValue.history }]} />
        </Reveal>
      )}

      <PlayerStats player={player} />

      {competitions.length > 0 && (
        <Reveal>
          <CompetitionStats lines={competitions} />
        </Reveal>
      )}

      {career && career.points.length >= 2 && (
        <Reveal>
          <CareerChart curve={career} color={accent} />
        </Reveal>
      )}

      {trend && trend.matches.length >= 3 ? (
        <Reveal>
          <TrendChart trend={trend} />
        </Reveal>
      ) : null}

      <section id="parecidos" className="flex scroll-mt-24 flex-col gap-5">
        <Reveal className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="font-heading text-2xl tracking-tight">Sus gemelos</h2>
            <p className="text-sm text-muted">
              {twins?.basic
                ? `Producen como él en su ${seasonDisplay(twins.target.season_label)}: de ${twins.target.competition} solo tenemos goles y asistencias.`
                : twins
                ? `Juegan como él en su ${seasonDisplay(twins.target.season_label)} con ${twins.target.team ?? twins.target.competition}. Pulsa uno para verlos cara a cara.`
                : "Jugadores con un estilo parecido."}
            </p>
          </div>
          <Link
            href={`/gemelos?p=${player.player_id}`}
            className="rounded-full bg-[#c93c17] px-4 py-2 text-sm font-bold text-bg transition hover:brightness-105"
          >
            Buscar gemelos baratos →
          </Link>
        </Reveal>
        <SimilarPlayers report={twins} />
      </section>
    </div>
  );
}
