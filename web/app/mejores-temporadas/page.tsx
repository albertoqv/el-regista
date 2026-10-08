import type { Metadata } from "next";
import Link from "next/link";
import { seasonDisplay } from "@/lib/format";
import type { MetricKey } from "@/lib/metrics";
import { latestYear, LINE_LABELS, LINES, loadProfiles, seasonKey, type Line, type Profile } from "@/lib/profiles";

export const metadata: Metadata = {
  title: "Mejores temporadas desde 2014 · El Regista",
  description: "Las mejores temporadas de las 5 grandes ligas desde 2014: goles, asistencias, xG, xA y más, en total o por 90 minutos.",
};

const LEAGUES = [
  { slug: "todas", label: "Las 5 ligas", competition: null },
  { slug: "la-liga", label: "LaLiga", competition: "La Liga" },
  { slug: "premier-league", label: "Premier League", competition: "Premier League" },
  { slug: "serie-a", label: "Serie A", competition: "Serie A" },
  { slug: "bundesliga", label: "Bundesliga", competition: "Bundesliga" },
  { slug: "ligue-1", label: "Ligue 1", competition: "Ligue 1" },
] as const;

const POSITIONS: { slug: string; label: string; lines: readonly Line[] }[] = [
  { slug: "todos", label: "Todos", lines: LINES },
  ...LINES.map((line) => ({ slug: LINE_LABELS[line].toLowerCase(), label: LINE_LABELS[line], lines: [line] })),
];

type Ranked = { slug: string; label: string; value: (profile: Profile) => number; decimals: number };

const sum = (...keys: MetricKey[]) => (profile: Profile) => keys.reduce((total, key) => total + profile.totals[key], 0);

const RANKINGS: Ranked[] = [
  { slug: "goles", label: "Goles", value: sum("goals"), decimals: 0 },
  { slug: "asistencias", label: "Asistencias", value: sum("assists"), decimals: 0 },
  { slug: "goles-asistencias", label: "Goles + asist.", value: sum("goals", "assists"), decimals: 0 },
  { slug: "xg", label: "xG", value: sum("expected_goals"), decimals: 1 },
  { slug: "xa", label: "xA", value: sum("expected_assists"), decimals: 1 },
  { slug: "pases-clave", label: "Pases clave", value: sum("key_passes"), decimals: 0 },
  { slug: "xgchain", label: "xGChain", value: sum("xg_chain"), decimals: 1 },
  { slug: "tiros", label: "Tiros", value: sum("shots"), decimals: 0 },
];

// Per 90 needs about half a season: below that a hot month tops the list.
const PER_90_MINUTES = 1800;
const LIMIT = 50;

function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function BestSeasonsPage(props: PageProps<"/mejores-temporadas">) {
  const searchParams = await props.searchParams;
  const league = LEAGUES.find((entry) => entry.slug === param(searchParams.liga)) ?? LEAGUES[0];
  const position = POSITIONS.find((entry) => entry.slug === param(searchParams.pos)) ?? POSITIONS[0];
  const ranking = RANKINGS.find((entry) => entry.slug === param(searchParams.metrica)) ?? RANKINGS[0];
  const per90 = param(searchParams.modo) === "p90";

  const profiles = await loadProfiles(position.lines);
  const latest = latestYear(profiles);
  const value = (profile: Profile) => (per90 ? (ranking.value(profile) * 90) / profile.minutes : ranking.value(profile));
  const rows = profiles
    .filter((profile) => !league.competition || profile.competition === league.competition)
    .filter((profile) => !per90 || profile.minutes >= PER_90_MINUTES)
    .sort((a, b) => value(b) - value(a))
    .slice(0, LIMIT);

  const link = (change: Record<string, string>) => {
    const query = new URLSearchParams({
      liga: league.slug,
      pos: position.slug,
      metrica: ranking.slug,
      modo: per90 ? "p90" : "total",
      ...change,
    });
    return `/mejores-temporadas?${query}`;
  };
  const chip = (active: boolean) =>
    `shrink-0 rounded-full px-3 py-1.5 text-sm font-medium ${active ? "bg-ink text-bg" : "text-muted hover:bg-ink/5 hover:text-ink"}`;

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-5xl leading-[0.92] sm:text-6xl">Mejores temporadas</h1>
        <p className="text-sm text-muted">
          Las 5 grandes ligas de la 14/15 a la {seasonDisplay(String(latest))}, con los datos de Understat. Solo temporadas
          terminadas{per90 ? ` y de ${PER_90_MINUTES.toLocaleString("es-ES")} minutos o más` : ""}.
        </p>
      </header>

      <nav aria-label="Métrica" className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
        {RANKINGS.map((entry) => (
          <Link
            key={entry.slug}
            href={link({ metrica: entry.slug })}
            aria-current={entry === ranking ? "page" : undefined}
            className={`shrink-0 rounded-lg px-4 py-2 text-sm font-semibold transition ${entry === ranking ? "bg-ink text-bg" : "glass glass-hover"}`}
          >
            {entry.label}
          </Link>
        ))}
      </nav>
      <div className="-mt-4 flex flex-col gap-2">
        {[
          { label: "Liga", items: LEAGUES.map((entry) => ({ key: entry.slug, label: entry.label, active: entry === league, href: link({ liga: entry.slug }) })) },
          { label: "Puesto", items: POSITIONS.map((entry) => ({ key: entry.slug, label: entry.label, active: entry === position, href: link({ pos: entry.slug }) })) },
          {
            label: "Cuenta",
            items: [
              { key: "total", label: "Total", active: !per90, href: link({ modo: "total" }) },
              { key: "p90", label: "Por 90 minutos", active: per90, href: link({ modo: "p90" }) },
            ],
          },
        ].map((group) => (
          <nav key={group.label} aria-label={group.label} className="flex items-center gap-2">
            <span className="w-16 shrink-0 text-sm font-semibold text-muted">{group.label}</span>
            <div className="no-scrollbar -mr-4 flex gap-1.5 overflow-x-auto pr-4 sm:mr-0 sm:flex-wrap sm:pr-0">
              {group.items.map((item) => (
                <Link key={item.key} href={item.href} aria-current={item.active ? "page" : undefined} className={chip(item.active)}>
                  {item.label}
                </Link>
              ))}
            </div>
          </nav>
        ))}
      </div>

      {rows.length === 0 ? (
        <p className="glass rounded-lg p-8 text-center text-sm text-muted">No hay datos ahora mismo.</p>
      ) : (
        <ol className="flex flex-col divide-y divide-line border-y border-line">
          {rows.map((profile, index) => (
            <li key={`${profile.id}-${seasonKey(profile)}`}>
              <Link
                href={`/epocas?j=${profile.id}&s=${seasonKey(profile)}`}
                className="flex items-center gap-3 px-1 py-3 transition hover:bg-ink/5 sm:gap-4 sm:px-3"
              >
                <span className="w-7 shrink-0 text-right font-heading text-base tabular-nums text-muted">{index + 1}</span>
                <span className="flex min-w-0 flex-1 flex-col">
                  <span className="truncate font-semibold">{profile.name}</span>
                  <span className="truncate text-xs text-muted">
                    {profile.team} · {profile.competition} {seasonDisplay(String(profile.year))} · {profile.minutes.toLocaleString("es-ES")}&apos;
                  </span>
                </span>
                {!per90 && (
                  <span className="hidden w-24 shrink-0 text-right text-xs text-muted sm:block">
                    {((ranking.value(profile) * 90) / profile.minutes).toFixed(2)} por 90&apos;
                  </span>
                )}
                <span className="w-16 shrink-0 text-right font-display text-3xl tabular-nums">
                  {value(profile).toFixed(per90 ? 2 : ranking.decimals)}
                </span>
              </Link>
            </li>
          ))}
        </ol>
      )}

      <p className="text-sm text-muted">
        Pulsa una temporada para ver su radar y quién juega igual hoy.
      </p>
    </div>
  );
}
