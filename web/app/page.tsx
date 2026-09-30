import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { DuelCard } from "@/app/components/DuelCard";
import { HandArrow, Marker, ScoutNote, Sticker } from "@/app/components/ScoutNote";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { Reveal } from "@/app/components/motion";
import { PlayerSearchForm } from "@/app/components/PlayerSearchForm";
import { Partnerships } from "@/app/components/Partnerships";
import { ProductBand, ProductsGrid } from "@/app/components/Products";
import { RoundHighlights } from "@/app/components/RoundHighlights";
import { SeasonLeaders } from "@/app/components/SeasonLeaders";
import { SeasonMoments } from "@/app/components/SeasonMoments";
import {
  findTwins,
  getHighlights,
  getHotPlayers,
  getOverview,
  getTrackRecord,
  listPartnerships,
  listSeasonLeaders,
  listShotLeaders,
  type Highlights,
  type HotBoard,
  type Overview,
  type Partnership,
  type SeasonLeader,
  type ShotLeader,
  type TrackRecord,
  type TwinReport,
} from "@/lib/api";
import { competitionColor, currentSeasonStartYear, formatMarketValue, seasonDisplay } from "@/lib/format";

async function loadHome(startYear: number) {
  try {
    const [scorers, creators, xg, moments, pairs, highlights, overview, hot, record] = await Promise.all([
      listSeasonLeaders(startYear, { metric: "goals", limit: 10 }),
      listSeasonLeaders(startYear, { metric: "expected_assists", limit: 2 }),
      listSeasonLeaders(startYear, { metric: "xg_chain", limit: 2 }),
      listShotLeaders(startYear, { metric: "late_goals", limit: 8 }).catch((): ShotLeader[] => []),
      listPartnerships(startYear, { limit: 6 }).catch((): Partnership[] => []),
      getHighlights(3).catch((): Highlights | null => null),
      getOverview().catch((): Overview | null => null),
      getHotPlayers({ limit: 5 }).catch((): HotBoard | null => null),
      getTrackRecord(startYear).catch((): TrackRecord | null => null),
    ]);
    // Live twin teaser: a standout attacker of the season and cheaper look-alikes.
    const star = [...xg, ...scorers].find((leader) => leader.photo_url) ?? scorers[0];
    const teaser = star
      ? await findTwins(star.player_id, { limit: 8 }).catch((): TwinReport | null => null)
      : null;
    return { scorers, creators, xg, teaser, moments, pairs, highlights, overview, hot, record, error: false };
  } catch {
    return {
      scorers: [],
      creators: [],
      xg: [],
      teaser: null,
      moments: [] as ShotLeader[],
      pairs: [] as Partnership[],
      highlights: null as Highlights | null,
      overview: null as Overview | null,
      hot: null as HotBoard | null,
      record: null as TrackRecord | null,
      error: true,
    };
  }
}

function duel(
  pair: SeasonLeader[],
  title: string,
): { title: string; a: SeasonLeader; b: SeasonLeader } | null {
  return pair.length >= 2 ? { title, a: pair[0], b: pair[1] } : null;
}

export default async function HomePage() {
  const startYear = currentSeasonStartYear();
  const { scorers, creators, xg, teaser, moments, pairs, highlights, overview, hot, record, error } =
    await loadHome(startYear);
  const duels = [
    duel(scorers, "Duelo de goleadores"),
    duel(creators, "Duelo de creadores"),
    duel(xg, "Los que más pesan en ataque"),
  ].filter((entry) => entry !== null);

  return (
    <div className="flex flex-col gap-20">
      <section className="relative flex flex-col items-center gap-7 pt-10 text-center sm:pt-16">
        <Reveal>
          <span className="glass inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-medium text-ink/80">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            Temporada {seasonDisplay(String(startYear))} · 14 ligas · se actualiza martes y viernes
          </span>
        </Reveal>
        <Reveal delay={0.08}>
          <h1 className="font-display text-5xl font-bold leading-[1.02] tracking-tight sm:text-7xl">
            Tu ojeador
            <br />
            de <Marker color="#3d8bff">bolsillo</Marker>.
          </h1>
        </Reveal>
        <Reveal delay={0.16}>
          <p className="max-w-2xl text-base text-muted sm:text-lg">
            <strong className="text-ink">Scout</strong> para descubrir y comparar jugadores.{" "}
            <strong className="text-ink">Pronósticos</strong> para saber qué puede pasar en cada
            partido. Con datos reales y sin pagar lo que cuesta el original.
          </p>
        </Reveal>
        <Reveal delay={0.24} className="w-full max-w-2xl">
          <PlayerSearchForm />
        </Reveal>
        <Reveal delay={0.3}>
          <Link
            href="/compare"
            className="text-sm font-medium text-brand-2 underline-offset-4 hover:underline"
          >
            o compara dos jugadores directamente →
          </Link>
        </Reveal>
        {overview && (
          <Reveal delay={0.35} className="mt-4 grid w-full max-w-3xl grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { value: overview.players, label: "jugadores" },
              { value: overview.competitions, label: "competiciones" },
              { value: overview.shots, label: "tiros analizados" },
              { value: overview.match_stats, label: "partidos con estadísticas" },
            ].map((item) => (
              <div key={item.label} className="glass rounded-2xl px-3 py-3">
                <span className="block font-display text-2xl font-bold tabular-nums">
                  {item.value.toLocaleString("es-ES")}
                </span>
                <span className="text-xs text-muted">{item.label}</span>
              </div>
            ))}
          </Reveal>
        )}
      </section>

      <Reveal>
        <ProductsGrid />
      </Reveal>

      {error && (
        <p className="glass rounded-2xl border-red-500/30 p-5 text-center text-sm text-red-300">
          No se ha podido conectar con los datos ahora mismo. Inténtalo en unos minutos.
        </p>
      )}

      <ProductBand product="scout" title="Lo que está pasando con los jugadores">
        {!error && (
          <Reveal>
            <SeasonLeaders startYear={startYear} initialLeaders={scorers} />
          </Reveal>
        )}

        {hot && hot.players.length > 0 && <HotTeaser board={hot} />}

        {teaser && teaser.twins.some((twin) => twin.market_value_eur !== null) && (
          <TwinTeaser report={teaser} />
        )}

        {moments.length > 0 && (
          <Reveal>
            <SeasonMoments startYear={startYear} initialLeaders={moments} />
          </Reveal>
        )}

        {duels.length > 0 && (
          <section className="flex flex-col gap-6">
            <Reveal>
              <h3 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">Duelos del momento</h3>
            </Reveal>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {duels.map((entry, index) => (
                <Reveal key={entry.title} delay={index * 0.08}>
                  <DuelCard title={entry.title} a={entry.a} b={entry.b} />
                </Reveal>
              ))}
            </div>
          </section>
        )}

        <Partnerships pairs={pairs} />
      </ProductBand>

      <ProductBand product="pronosticos" title="Lo que puede pasar en los partidos">
        {highlights && highlights.picks.length > 0 && (
          <Reveal>
            <RoundHighlights highlights={highlights} compact />
            <div className="mt-3 text-center">
              <Link href="/predicciones" className="text-sm font-semibold text-emerald-300 hover:underline">
                Ver todos los partidos →
              </Link>
            </div>
          </Reveal>
        )}
        {record && <RecordTeaser record={record} />}
      </ProductBand>
    </div>
  );
}

function HotTeaser({ board }: { board: HotBoard }) {
  return (
    <Reveal>
      <div className="glass rounded-[2rem] p-5 sm:p-7">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <Sticker tone="yellow" rotate={-2} className="w-fit">
              En racha
            </Sticker>
            <h3 className="mt-2 font-display text-2xl font-bold tracking-tight sm:text-3xl">
              Los más en forma del último mes
            </h3>
          </div>
          <Link href="/en-racha" className="text-sm font-semibold text-brand-2 hover:underline">
            Ranking completo →
          </Link>
        </div>
        <ol className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-5">
          {board.players.map((player, index) => {
            const content = (
              <>
                <span className="font-display text-lg font-bold text-muted">{index + 1}</span>
                <Avatar name={player.name} photoUrl={player.photo_url} size={40} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold">{player.name}</span>
                  <span className="flex items-center gap-1 truncate text-xs text-muted">
                    <span
                      className="h-1.5 w-1.5 shrink-0 rounded-full"
                      style={{ background: competitionColor(player.competition) }}
                    />
                    {player.team}
                  </span>
                </span>
                <span className="font-display text-xl font-bold text-[#ffd76a]">
                  {player.goals + player.assists}
                </span>
              </>
            );
            return (
              <li key={player.understat_player_id}>
                {player.player_id ? (
                  <Link
                    href={`/players/${player.player_id}`}
                    className="flex items-center gap-2.5 rounded-2xl border border-line p-2.5 transition hover:bg-white/[0.04]"
                  >
                    {content}
                  </Link>
                ) : (
                  <div className="flex items-center gap-2.5 rounded-2xl border border-line p-2.5">{content}</div>
                )}
              </li>
            );
          })}
        </ol>
        <p className="mt-2 text-xs text-muted">Goles + asistencias en los últimos 30 días.</p>
      </div>
    </Reveal>
  );
}

function RecordTeaser({ record }: { record: TrackRecord }) {
  const live = record.live_total.matches > 0;
  const totals = live ? record.live_total : record.rebuilt_total;
  if (totals.matches === 0) return null;
  const rate = Math.round((totals.hits / totals.matches) * 100);
  const confident = totals.confident
    ? Math.round((totals.confident_hits / totals.confident) * 100)
    : null;
  return (
    <Reveal>
      <Link
        href="/predicciones/historial"
        className="glass glass-hover grid grid-cols-1 items-center gap-5 rounded-[2rem] p-5 sm:grid-cols-[1fr_auto_auto] sm:p-7"
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">
            Historial de aciertos
          </p>
          <h3 className="font-display text-2xl font-bold tracking-tight">
            {live
              ? "Predicciones guardadas antes del partido"
              : `La ${seasonDisplay(record.season_label)} reconstruida sin mirar el futuro`}
          </h3>
          <p className="mt-1 text-sm text-muted">
            {totals.matches} partidos puntuados. Míralos uno a uno →
          </p>
        </div>
        <div className="text-center">
          <span className="block font-display text-5xl font-bold text-emerald-300">{rate}%</span>
          <span className="text-xs text-muted">aciertos 1X2 (azar 33%)</span>
        </div>
        {confident !== null ? (
          <div className="text-center">
            <span className="block font-display text-5xl font-bold text-[#ffd76a]">{confident}%</span>
            <span className="text-xs text-muted">cuando damos 60% o más</span>
          </div>
        ) : null}
      </Link>
    </Reveal>
  );
}

function TwinTeaser({ report }: { report: TwinReport }) {
  const { target } = report;
  const cheap = report.twins
    .filter((twin) => twin.market_value_eur !== null && (!target.market_value_eur || twin.market_value_eur < target.market_value_eur))
    .slice(0, 3);
  if (cheap.length === 0) return null;

  return (
    <section className="relative">
      <Reveal>
        <div className="glass relative overflow-hidden rounded-[2rem] p-6 sm:p-10">
          <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-[1fr_1.3fr]">
            <div className="flex flex-col gap-4">
              <Sticker tone="yellow" rotate={-3} className="w-fit">Lo más buscado</Sticker>
              <h2 className="font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
                ¿{target.name}
                {target.market_value_eur ? ` por ${formatMarketValue(target.market_value_eur)}` : ""}?
                <br />
                <span className="text-[#ffd76a]">Tenemos gemelos.</span>
              </h2>
              <p className="text-muted">
                Jugadores que hacen lo mismo cada 90 minutos, por una fracción del precio. Busca los
                de cualquier jugador.
              </p>
              <Link
                href={`/gemelos?p=${target.player_id}`}
                className="w-fit rounded-full bg-[#ffd76a] px-6 py-3 font-bold text-black transition hover:brightness-105"
              >
                Ver todos sus gemelos →
              </Link>
            </div>
            <div className="relative grid grid-cols-3 gap-3">
              {cheap.map((twin, index) => (
                <Link key={twin.player_id} href={`/gemelos?p=${target.player_id}#twin-${twin.player_id}`} className="group relative block" style={{ transform: `rotate(${[-2, 1.5, -1][index]}deg)` }}>
                  <PlayerPortrait
                    name={twin.name}
                    photoUrl={twin.photo_url}
                    accent="#ffd76a"
                    rounded="rounded-2xl"
                    className="aspect-[3/4] transition duration-500 group-hover:-translate-y-1"
                  />
                  <span className="absolute right-2 top-2 rounded-full bg-black/65 px-2 py-0.5 font-display text-sm font-bold">
                    {twin.similarity}%
                  </span>
                  <div className="absolute inset-x-0 bottom-0 p-3">
                    <span className="block truncate text-sm font-bold">{twin.name}</span>
                    <span className="font-display text-lg font-bold text-emerald-300">
                      {formatMarketValue(twin.market_value_eur as number)}
                    </span>
                  </div>
                </Link>
              ))}
              <span className="pointer-events-none absolute -bottom-10 right-4 hidden items-center gap-1 text-[#ffd76a] sm:flex">
                <HandArrow direction="right" className="-scale-x-100" />
                <ScoutNote rotate={-3}>mismo estilo, otro precio</ScoutNote>
              </span>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
