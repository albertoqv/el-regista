import Link from "next/link";
import { notFound } from "next/navigation";
import { MarketValueChart } from "@/app/components/MarketValueChart";
import { CountUp, Reveal } from "@/app/components/motion";
import { PercentileBars, PercentileLegend } from "@/app/components/PercentileBars";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { PlayerStats } from "@/app/components/PlayerStats";
import { RadarChart } from "@/app/components/RadarChart";
import { SeasonSelector } from "@/app/components/SeasonSelector";
import { SimilarPlayers } from "@/app/components/SimilarPlayers";
import {
  ApiError,
  findSimilarPlayers,
  getMarketValue,
  getPlayer,
  getPlayerPercentiles,
  getPlayerSeason,
  listPlayerSeasons,
  type MarketValueHistory,
  type PercentileReport,
  type Season,
  type SimilarPlayerMatch,
} from "@/lib/api";
import {
  competitionColor,
  footLabel,
  formatAge,
  formatMarketValue,
  positionLabel,
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
    <div className="glass flex flex-col rounded-2xl px-4 py-2.5">
      <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted">
        {label}
      </span>
      <span className="font-display text-base font-semibold">{value}</span>
    </div>
  );
}

export default async function PlayerDetailPage(props: PageProps<"/players/[id]">) {
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

  const [similar, marketValue, percentiles] = await Promise.all([
    findSimilarPlayers(playerId, { season: season ?? undefined, top: 6 }).catch(
      () => [] as SimilarPlayerMatch[],
    ),
    getMarketValue(playerId).catch(
      (): MarketValueHistory => ({ current: null, history: [] }),
    ),
    season
      ? getPlayerPercentiles(playerId, season).catch(() => null)
      : Promise.resolve<PercentileReport | null>(null),
  ]);

  const age = formatAge(player);
  const team = season ? seasons.find((s) => s.label === season.label && s.competition === season.competition)?.team : null;
  const accent = season ? competitionColor(season.competition) : "#3d8bff";
  const contributions = player.goals + player.assists;

  return (
    <div className="flex flex-col gap-14">
      <section className="relative">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -top-6 left-0 right-0 select-none overflow-hidden whitespace-nowrap text-center font-display text-[18vw] font-bold uppercase leading-none text-white/[0.03] sm:text-[9rem]"
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
            />
          </Reveal>

          <div className="flex flex-col gap-5">
            <Reveal delay={0.05}>
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.25em]" style={{ color: accent }}>
                {positionLabel(player.position)}
                {team && <span className="text-muted">· {team}</span>}
              </p>
              <h1 className="font-display text-5xl font-bold leading-none tracking-tight sm:text-6xl">
                {player.name}
              </h1>
            </Reveal>

            <Reveal delay={0.1} className="flex flex-wrap gap-2">
              {age && <Badge label="Edad" value={`${age} años`} />}
              {player.preferred_foot && <Badge label="Pie" value={footLabel(player.preferred_foot)} />}
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
                <div key={stat.label} className="glass rounded-3xl p-4">
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
                className="rounded-full bg-gradient-to-r from-brand to-brand-2 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_0_24px_rgba(61,139,255,0.45)] transition hover:brightness-110"
              >
                Comparar con otro jugador
              </Link>
              <a
                href="#parecidos"
                className="glass rounded-full px-5 py-2.5 text-sm font-semibold transition hover:border-line-strong"
              >
                Ver jugadores parecidos
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
          <section className="glass grid grid-cols-1 gap-8 rounded-3xl p-6 lg:grid-cols-2">
            <div className="flex flex-col gap-3">
              <div>
                <h2 className="font-display text-2xl font-bold tracking-tight">
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

      {marketValue.history.length > 0 && (
        <Reveal>
          <MarketValueChart series={[{ name: player.name, color: "#22d3ee", history: marketValue.history }]} />
        </Reveal>
      )}

      <PlayerStats player={player} />

      <section id="parecidos" className="flex scroll-mt-24 flex-col gap-5">
        <Reveal>
          <h2 className="font-display text-2xl font-bold tracking-tight">
            Jugadores con un perfil parecido
          </h2>
          <p className="text-sm text-muted">
            {season
              ? `Según sus números en ${season.competition} ${seasonDisplay(season.label)}. Pulsa uno para verlos cara a cara.`
              : "Según sus números de toda la carrera. Pulsa uno para verlos cara a cara."}
          </p>
        </Reveal>
        <SimilarPlayers player={player} season={season} matches={similar} />
      </section>
    </div>
  );
}
