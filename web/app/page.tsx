import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { Reveal } from "@/app/components/motion";
import { PlayerSearchForm } from "@/app/components/PlayerSearchForm";
import { ProductBand, ProductsGrid } from "@/app/components/Products";
import { RoundHighlights } from "@/app/components/RoundHighlights";
import { SeasonLeaders } from "@/app/components/SeasonLeaders";
import { Sticker } from "@/app/components/ScoutNote";
import {
  findTwins,
  getHighlights,
  getHotPlayers,
  getOverview,
  getTrackRecord,
  listSeasonLeaders,
  type Highlights,
  type HotBoard,
  type Overview,
  type TrackRecord,
  type TwinReport,
} from "@/lib/api";
import { currentSeasonStartYear, formatMarketValue, seasonDisplay } from "@/lib/format";
import { PHOTOS } from "@/lib/photos";

async function loadHome(startYear: number) {
  try {
    const [scorers, xg, highlights, overview, hot, record] = await Promise.all([
      listSeasonLeaders(startYear, { metric: "goals", limit: 10 }),
      listSeasonLeaders(startYear, { metric: "xg_chain", limit: 2 }),
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
    return { scorers, teaser, highlights, overview, hot, record, error: false };
  } catch {
    return {
      scorers: [],
      teaser: null,
      highlights: null as Highlights | null,
      overview: null as Overview | null,
      hot: null as HotBoard | null,
      record: null as TrackRecord | null,
      error: true,
    };
  }
}

export default async function HomePage() {
  const startYear = currentSeasonStartYear();
  const { scorers, teaser, highlights, overview, hot, record, error } = await loadHome(startYear);

  return (
    <div className="flex flex-col gap-16">
      <section className="photo-header -mx-4 -mt-6 flex min-h-[460px] flex-col justify-end gap-6 px-4 pb-10 pt-24 sm:mx-0 sm:mt-0 sm:rounded-xl sm:px-10">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={PHOTOS.portada.src} alt="" className="slow-zoom" fetchPriority="high" />
        <div className="flex flex-col gap-3">
          <Sticker className="w-fit">Temporada {seasonDisplay(String(startYear))}</Sticker>
          <h1 className="font-display text-5xl leading-[0.92] sm:text-7xl">
            Fútbol con
            <br />
            datos de verdad
          </h1>
          <p className="max-w-xl text-base text-ink/85">Jugadores y partidos de 14 ligas, contados con números reales.</p>
        </div>
        <div className="w-full max-w-2xl">
          <PlayerSearchForm />
        </div>
        {overview && (
          <dl className="flex flex-wrap gap-x-10 gap-y-3">
            {[
              { value: overview.players, label: "jugadores" },
              { value: overview.shots, label: "tiros" },
              { value: overview.match_stats, label: "partidos" },
            ].map((item) => (
              <div key={item.label} className="flex items-baseline gap-2">
                <dt className="sr-only">{item.label}</dt>
                <dd className="font-display text-3xl tabular-nums">{item.value.toLocaleString("es-ES")}</dd>
                <span className="text-sm text-muted">{item.label}</span>
              </div>
            ))}
          </dl>
        )}
      </section>

      <Reveal>
        <ProductsGrid />
      </Reveal>

      {error && (
        <p className="glass rounded-lg p-5 text-center text-sm text-side-b">
          No hay conexión con los datos ahora mismo. Prueba en unos minutos.
        </p>
      )}

      <ProductBand product="scout" title="Scout">
        {!error && (
          <Reveal>
            <SeasonLeaders startYear={startYear} initialLeaders={scorers} />
          </Reveal>
        )}
        {hot && hot.players.length > 0 && <HotTeaser board={hot} />}
        {teaser && teaser.twins.some((twin) => twin.market_value_eur !== null) && (
          <TwinTeaser report={teaser} />
        )}
      </ProductBand>

      <ProductBand product="pronosticos" title="Pronósticos">
        {highlights && highlights.picks.length > 0 && (
          <Reveal>
            <RoundHighlights highlights={highlights} compact />
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
      <div className="glass rounded-xl p-5 sm:p-7">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h3 className="mt-2 font-display text-2xl font-bold tracking-tight sm:text-3xl">
              En racha
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
                    {player.team}
                  </span>
                </span>
                <span className="font-display text-xl font-bold text-[#9ccfea]">
                  {player.goals + player.assists}
                </span>
              </>
            );
            return (
              <li key={player.understat_player_id}>
                {player.player_id ? (
                  <Link
                    href={`/players/${player.player_id}`}
                    className="flex items-center gap-2.5 rounded-lg border border-line p-2.5 transition hover:bg-white/[0.04]"
                  >
                    {content}
                  </Link>
                ) : (
                  <div className="flex items-center gap-2.5 rounded-lg border border-line p-2.5">{content}</div>
                )}
              </li>
            );
          })}
        </ol>
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
        className="glass glass-hover grid grid-cols-1 items-center gap-5 rounded-xl p-5 sm:grid-cols-[1fr_auto_auto] sm:p-7"
      >
        <div>
          <p className="text-xs font-semibold text-brand-2">
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
          <span className="block font-display text-5xl font-bold text-brand-2">{rate}%</span>
          <span className="text-xs text-muted">aciertos 1X2 (azar 33%)</span>
        </div>
        {confident !== null ? (
          <div className="text-center">
            <span className="block font-display text-5xl font-bold text-[#9ccfea]">{confident}%</span>
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
        <div className="glass relative overflow-hidden rounded-xl p-6 sm:p-10">
          <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-[1fr_1.3fr]">
            <div className="flex flex-col gap-4">
              <Sticker tone="yellow" rotate={-3} className="w-fit">Lo más buscado</Sticker>
              <h2 className="font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
                ¿{target.name}
                {target.market_value_eur ? ` por ${formatMarketValue(target.market_value_eur)}` : ""}?
                <br />
                <span className="text-[#9ccfea]">Tenemos gemelos.</span>
              </h2>
              <Link
                href={`/gemelos?p=${target.player_id}`}
                className="w-fit rounded-full bg-[#9ccfea] px-6 py-3 font-bold text-bg transition hover:brightness-105"
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
                    accent="#9ccfea"
                    rounded="rounded-lg"
                    className="aspect-[3/4] transition duration-500 group-hover:-translate-y-1"
                  />
                  <span className="absolute right-2 top-2 rounded-full bg-black/65 px-2 py-0.5 font-display text-sm font-bold">
                    {twin.similarity}%
                  </span>
                  <div className="absolute inset-x-0 bottom-0 p-3">
                    <span className="block truncate text-sm font-bold">{twin.name}</span>
                    <span className="font-display text-lg font-bold text-brand-2">
                      {formatMarketValue(twin.market_value_eur as number)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
