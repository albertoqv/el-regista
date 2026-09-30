import Link from "next/link";
import { DuelCard } from "@/app/components/DuelCard";
import { IconCreate, IconSearch, IconTarget } from "@/app/components/icons";
import { HandArrow, Marker, ScoutNote, Sticker } from "@/app/components/ScoutNote";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { Reveal } from "@/app/components/motion";
import { PlayerSearchForm } from "@/app/components/PlayerSearchForm";
import { Partnerships } from "@/app/components/Partnerships";
import { RoundHighlights } from "@/app/components/RoundHighlights";
import { SeasonLeaders } from "@/app/components/SeasonLeaders";
import { SeasonMoments } from "@/app/components/SeasonMoments";
import {
  findTwins,
  getHighlights,
  getOverview,
  listPartnerships,
  listSeasonLeaders,
  listShotLeaders,
  type Highlights,
  type Overview,
  type Partnership,
  type SeasonLeader,
  type ShotLeader,
  type TwinReport,
} from "@/lib/api";
import { currentSeasonStartYear, formatMarketValue, seasonDisplay } from "@/lib/format";

async function loadHome(startYear: number) {
  try {
    const [scorers, creators, xg, moments, pairs, highlights, overview] = await Promise.all([
      listSeasonLeaders(startYear, { metric: "goals", limit: 10 }),
      listSeasonLeaders(startYear, { metric: "expected_assists", limit: 2 }),
      listSeasonLeaders(startYear, { metric: "xg_chain", limit: 2 }),
      listShotLeaders(startYear, { metric: "late_goals", limit: 8 }).catch((): ShotLeader[] => []),
      listPartnerships(startYear, { limit: 6 }).catch((): Partnership[] => []),
      getHighlights(3).catch((): Highlights | null => null),
      getOverview().catch((): Overview | null => null),
    ]);
    // Live twin teaser: a standout attacker of the season and cheaper look-alikes.
    const star = [...xg, ...scorers].find((leader) => leader.photo_url) ?? scorers[0];
    const teaser = star
      ? await findTwins(star.player_id, { limit: 8 }).catch((): TwinReport | null => null)
      : null;
    return { scorers, creators, xg, teaser, moments, pairs, highlights, overview, error: false };
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

const FEATURES = [
  {
    href: "/compare",
    icon: IconTarget,
    title: "Cara a cara",
    text: "Dos jugadores enfrentados: quién gana en cada faceta, por 90 minutos y con veredicto.",
  },
  {
    href: "/compare",
    icon: IconCreate,
    title: "Radar de percentiles",
    text: "Cada jugador frente a los de su puesto y su liga, como en los informes de scouting profesionales.",
  },
  {
    href: "/gemelos",
    icon: IconSearch,
    title: "Encuentra al gemelo",
    text: "Busca jugadores con un perfil estadístico parecido: el recambio ideal, en cualquier liga.",
  },
];

export default async function HomePage() {
  const startYear = currentSeasonStartYear();
  const { scorers, creators, xg, teaser, moments, pairs, highlights, overview, error } =
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
            Temporada {seasonDisplay(String(startYear))} · 5 grandes ligas · actualizado cada semana
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
            Mira quién está rindiendo de verdad, enfréntalos cara a cara y encuentra al
            próximo crack antes que nadie. Y sin pagar lo que cuesta el original.
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

      {error && (
        <p className="glass rounded-2xl border-red-500/30 p-5 text-center text-sm text-red-300">
          No se ha podido conectar con los datos ahora mismo. Inténtalo en unos minutos.
        </p>
      )}

      {!error && (
        <Reveal>
          <SeasonLeaders startYear={startYear} initialLeaders={scorers} />
        </Reveal>
      )}

      {highlights && highlights.picks.length > 0 && (
        <Reveal>
          <RoundHighlights highlights={highlights} compact />
          <div className="mt-3 text-center">
            <Link href="/predicciones" className="text-sm font-semibold text-brand-2 hover:underline">
              Ver todas las predicciones →
            </Link>
          </div>
        </Reveal>
      )}

      {moments.length > 0 && (
        <Reveal>
          <SeasonMoments startYear={startYear} initialLeaders={moments} />
        </Reveal>
      )}

      {teaser && teaser.twins.some((twin) => twin.market_value_eur !== null) && (
        <TwinTeaser report={teaser} />
      )}

      {duels.length > 0 && (
        <section className="flex flex-col gap-6">
          <Reveal>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-side-b">
              Cara a cara
            </p>
            <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
              Duelos del momento
            </h2>
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

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {FEATURES.map((feature, index) => (
          <Reveal key={feature.title} delay={index * 0.08}>
            <Link href={feature.href} className="glass glass-hover block h-full rounded-3xl p-6">
              <span className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-brand/15">
                <feature.icon size={22} color="#9cc3ff" />
              </span>
              <h3 className="font-display text-lg font-semibold">{feature.title}</h3>
              <p className="mt-1 text-sm text-muted">{feature.text}</p>
              <span className="mt-3 inline-block text-sm font-semibold text-brand-2">Probar →</span>
            </Link>
          </Reveal>
        ))}
      </section>
    </div>
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
