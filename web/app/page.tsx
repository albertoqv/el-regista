import Link from "next/link";
import { DuelCard } from "@/app/components/DuelCard";
import { IconCreate, IconSearch, IconTarget } from "@/app/components/icons";
import { Reveal } from "@/app/components/motion";
import { PlayerSearchForm } from "@/app/components/PlayerSearchForm";
import { SeasonLeaders } from "@/app/components/SeasonLeaders";
import { listSeasonLeaders, type SeasonLeader } from "@/lib/api";
import { currentSeasonStartYear, seasonDisplay } from "@/lib/format";

async function loadHome(startYear: number) {
  try {
    const [scorers, creators, xg] = await Promise.all([
      listSeasonLeaders(startYear, { metric: "goals", limit: 10 }),
      listSeasonLeaders(startYear, { metric: "expected_assists", limit: 2 }),
      listSeasonLeaders(startYear, { metric: "xg_chain", limit: 2 }),
    ]);
    return { scorers, creators, xg, error: false };
  } catch {
    return { scorers: [], creators: [], xg: [], error: true };
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
    icon: IconTarget,
    title: "Cara a cara",
    text: "Dos jugadores enfrentados: quién gana en cada faceta, por 90 minutos y con veredicto.",
  },
  {
    icon: IconCreate,
    title: "Radar de percentiles",
    text: "Cada jugador frente a los de su puesto y su liga, como en los informes de scouting profesionales.",
  },
  {
    icon: IconSearch,
    title: "Encuentra al gemelo",
    text: "Busca jugadores con un perfil estadístico parecido: el recambio ideal, en cualquier liga.",
  },
];

export default async function HomePage() {
  const startYear = currentSeasonStartYear();
  const { scorers, creators, xg, error } = await loadHome(startYear);
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
            Scouting de élite,
            <br />
            <span className="text-gradient">al alcance de todos.</span>
          </h1>
        </Reveal>
        <Reveal delay={0.16}>
          <p className="max-w-2xl text-base text-muted sm:text-lg">
            Compara futbolistas cara a cara, mira dónde destacan frente a los de su
            puesto y encuentra jugadores con su mismo perfil. Con datos reales.
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

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {FEATURES.map((feature, index) => (
          <Reveal key={feature.title} delay={index * 0.08}>
            <div className="glass glass-hover h-full rounded-3xl p-6">
              <span className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-brand/15">
                <feature.icon size={22} color="#9cc3ff" />
              </span>
              <h3 className="font-display text-lg font-semibold">{feature.title}</h3>
              <p className="mt-1 text-sm text-muted">{feature.text}</p>
            </div>
          </Reveal>
        ))}
      </section>
    </div>
  );
}
