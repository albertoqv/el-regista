import type { Metadata } from "next";
import Link from "next/link";
import { Reveal } from "@/app/components/Reveal";
import { PlayerPortrait } from "@/app/components/PlayerPortrait";
import { HandArrow, Marker, ScoutNote } from "@/app/components/ScoutNote";
import { TwinCard } from "@/app/components/TwinCard";
import { TwinSearch } from "@/app/components/TwinSearch";
import { ValueMap } from "@/app/components/ValueMap";
import { ApiError, findTwins, listSeasonLeaders, type SeasonLeader, type TwinReport } from "@/lib/api";
import {
  COMPETITIONS,
  competitionColor,
  currentSeasonStartYear,
  formatAge,
  formatMarketValue,
  positionLabel,
  seasonDisplay,
} from "@/lib/format";
import { AGES, BUDGETS } from "@/lib/twins";

export const metadata: Metadata = {
  title: "Gemelos · El Regista",
  description: "Encuentra jugadores con el mismo perfil que tu favorito, por mucho menos dinero.",
};

type Filters = { p: number; max: number | null; age: number | null; liga: string | null };

function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function href(filters: Filters, change: Partial<Filters>): string {
  const next = { ...filters, ...change };
  const params = new URLSearchParams({ p: String(next.p) });
  if (next.max) params.set("max", String(next.max));
  if (next.age) params.set("age", String(next.age));
  if (next.liga) params.set("liga", next.liga);
  return `/gemelos?${params.toString()}`;
}

function Chip({ active, href: to, children }: { active: boolean; href: string; children: React.ReactNode }) {
  return (
    <Link
      href={to}
      scroll={false}
      className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
        active ? "border-[#c93c17] bg-[#c93c17] text-bg" : "border-line text-muted hover:border-line-strong hover:text-ink"
      }`}
    >
      {children}
    </Link>
  );
}

async function starters(): Promise<SeasonLeader[]> {
  // Well-known attacking players from the last full season, to try it in one click.
  const year = currentSeasonStartYear() - 1;
  return listSeasonLeaders(year, { metric: "xg_chain", limit: 10 }).catch(() => []);
}

function Landing({ stars }: { stars: SeasonLeader[] }) {
  return (
    <div className="flex flex-col gap-12">
      <section className="relative flex flex-col items-center gap-6 pt-10 text-center sm:pt-14">
        <Reveal>
          <ScoutNote rotate={-4}>el truco de los ojeadores</ScoutNote>
          <h1 className="mt-2 font-display text-5xl font-bold leading-[1.02] tracking-tight sm:text-7xl">
            Encuentra al <Marker color="#c93c17">gemelo</Marker>.
          </h1>
        </Reveal>
        <Reveal delay={0.08}>
          <p className="max-w-2xl text-base text-muted sm:text-lg">Mismo estilo de juego, menos dinero.</p>
        </Reveal>
        <Reveal delay={0.14} className="relative w-full max-w-2xl">
          <TwinSearch autoFocus />
          <span className="pointer-events-none absolute -right-28 -top-12 hidden text-[#c93c17] lg:flex lg:items-end">
            <ScoutNote rotate={6}>prueba con tu crack</ScoutNote>
            <HandArrow direction="down-left" />
          </span>
        </Reveal>
      </section>

      {stars.length > 0 && (
        <section className="flex flex-col gap-4">
          <h2 className="font-heading text-xl">O empieza por uno de estos</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {stars.map((star, index) => (
              <Reveal key={star.player_id} delay={index * 0.04}>
                <Link href={`/gemelos?p=${star.player_id}`} className="group relative block">
                  <PlayerPortrait
                    name={star.name}
                    photoUrl={star.photo_url}
                    accent={competitionColor(star.competition)}
                    rounded="rounded-lg"
                    className="aspect-[3/4] transition duration-500 group-hover:-translate-y-1 group-hover:rotate-[-1deg]"
                  />
                  <div className="absolute inset-x-0 bottom-0 p-3">
                    <span className="block truncate font-heading text-sm">{star.name}</span>
                    <span className="block truncate text-xs text-muted">{star.team}</span>
                  </div>
                </Link>
              </Reveal>
            ))}
          </div>
        </section>
      )}

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {[
          ["1", "Elige a tu jugador", "El que ficharías si el dinero no importara."],
          ["2", "Leemos su estilo", "Qué hace cada 90 minutos comparado con los de su puesto: goles, pases clave, presión, participación…"],
          ["3", "Te damos gemelos", "Jugadores que hacen lo mismo, con su precio, el ahorro y en qué se parecen de verdad."],
        ].map(([step, title, text], index) => (
          <Reveal key={step} delay={index * 0.06}>
            <div className="glass h-full rounded-lg p-6">
              <span className="font-hand text-4xl text-[#c93c17]">{step}.</span>
              <h3 className="font-heading text-lg">{title}</h3>
              <p className="mt-1 text-sm text-muted">{text}</p>
            </div>
          </Reveal>
        ))}
      </section>
    </div>
  );
}

export default async function TwinsPage(props: PageProps<"/gemelos">) {
  const searchParams = await props.searchParams;
  const playerId = Number(param(searchParams.p));
  if (!playerId) {
    return <Landing stars={await starters()} />;
  }

  const filters: Filters = {
    p: playerId,
    max: Number(param(searchParams.max)) || null,
    age: Number(param(searchParams.age)) || null,
    liga: param(searchParams.liga) ?? null,
  };

  let report: TwinReport | null = null;
  let error: string | null = null;
  try {
    report = await findTwins(playerId, {
      maxValue: filters.max ?? undefined,
      maxAge: filters.age ?? undefined,
      league: filters.liga ?? undefined,
      limit: 24,
    });
  } catch (thrown) {
    error =
      thrown instanceof ApiError && thrown.status === 404
        ? "No tenemos suficientes datos de este jugador para buscarle gemelos."
        : "No se han podido buscar gemelos ahora mismo. Prueba en un momento.";
  }

  if (!report) {
    return (
      <div className="flex flex-col gap-6 pt-10">
        <TwinSearch />
        <p className="glass rounded-lg p-5 text-sm text-red-300">{error}</p>
      </div>
    );
  }

  const { target, twins } = report;
  const age = formatAge(target);
  const cheaper = twins.filter(
    (twin) => target.market_value_eur && twin.market_value_eur !== null && twin.market_value_eur < target.market_value_eur,
  );
  const best = cheaper.sort((a, b) => b.similarity - a.similarity)[0];

  return (
    <div className="flex flex-col gap-10">
      <div className="max-w-xl">
        <TwinSearch />
      </div>

      <section className="grid grid-cols-1 items-center gap-8 md:grid-cols-[260px_1fr]">
        <Reveal>
          <PlayerPortrait
            name={target.name}
            photoUrl={target.photo_url}
            accent="#c93c17"
            className="mx-auto aspect-[3/4] w-full max-w-[260px]"
          />
        </Reveal>
        <div className="flex flex-col gap-4">
          <Reveal>
            <ScoutNote rotate={-2}>buscando gemelos de…</ScoutNote>
            <h1 className="font-display text-5xl font-bold leading-none tracking-tight sm:text-6xl">
              {target.name}
            </h1>
            <p className="mt-2 text-sm text-muted">
              {positionLabel(target.position)} · {target.team ?? target.competition}{" "}
              {seasonDisplay(target.season_label)}
              {age && ` · ${age} años`}
            </p>
          </Reveal>
          <Reveal delay={0.06} className="flex flex-wrap items-end gap-6">
            <div>
              <span className="block text-xs font-semibold text-muted">
                Lo que cuesta
              </span>
              <span className="font-display text-5xl font-bold text-[#c93c17]">
                {target.market_value_eur ? formatMarketValue(target.market_value_eur) : "—"}
              </span>
            </div>
            {best && best.market_value_eur !== null && target.market_value_eur && (
              <div className="glass rounded-lg px-4 py-3">
                <span className="block text-xs font-semibold text-muted">
                  Mejor alternativa
                </span>
                <span className="font-heading text-lg">
                  {best.name} · {best.similarity}% por {formatMarketValue(best.market_value_eur)}
                </span>
              </div>
            )}
          </Reveal>
          <Reveal delay={0.1}>
            <Link
              href={`/players/${target.player_id}`}
              className="text-sm font-semibold text-brand-2 underline-offset-4 hover:underline"
            >
              Ver su ficha completa →
            </Link>
            {report.basic && (
              <p className="mt-2 max-w-xl text-sm text-muted">
                De {target.competition} solo tenemos goles y asistencias: se parecen en lo que
                producen, no en su estilo.
              </p>
            )}
          </Reveal>
        </div>
      </section>

      <section className="glass flex flex-col gap-3 rounded-lg p-4">
        <div className="no-scrollbar -mx-1 flex items-center gap-2 overflow-x-auto px-1">
          <span className="shrink-0 pr-1 text-xs font-semibold text-muted">Presupuesto</span>
          {BUDGETS.map((budget) => (
            <Chip key={budget.label} active={filters.max === budget.value} href={href(filters, { max: budget.value })}>
              {budget.label}
            </Chip>
          ))}
        </div>
        <div className="no-scrollbar -mx-1 flex items-center gap-2 overflow-x-auto px-1">
          <span className="shrink-0 pr-1 text-xs font-semibold text-muted">Edad</span>
          {AGES.map((option) => (
            <Chip key={option.label} active={filters.age === option.value} href={href(filters, { age: option.value })}>
              {option.label}
            </Chip>
          ))}
        </div>
        <div className="no-scrollbar -mx-1 flex items-center gap-2 overflow-x-auto px-1">
          <span className="shrink-0 pr-1 text-xs font-semibold text-muted">Liga</span>
          <Chip active={filters.liga === null} href={href(filters, { liga: null })}>
            Todas
          </Chip>
          {COMPETITIONS.map((league) => (
            <Chip key={league} active={filters.liga === league} href={href(filters, { liga: league })}>
              {league}
            </Chip>
          ))}
        </div>
      </section>

      {twins.length === 0 ? (
        <p className="glass rounded-lg p-8 text-center text-muted">
          <ScoutNote rotate={-2}>nada por aquí…</ScoutNote>
          <br />
          Ningún jugador cumple esos filtros. Prueba a subir el presupuesto o quitar la edad.
        </p>
      ) : (
        <>
          <Reveal>
            <ValueMap target={target} twins={twins} />
          </Reveal>
          <section className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {twins.map((twin, index) => (
              <Reveal key={twin.player_id} delay={(index % 3) * 0.06}>
                <div id={`twin-${twin.player_id}`} className="h-full scroll-mt-24">
                  <TwinCard target={target} twin={twin} rank={index} />
                </div>
              </Reveal>
            ))}
          </section>
          <p className="text-center text-xs text-muted">
            Parecido = estilo por cada 90 minutos frente a jugadores de su mismo puesto y liga
            (percentiles). Solo cuentan temporadas recientes con al menos 900 minutos.
          </p>
        </>
      )}
    </div>
  );
}
