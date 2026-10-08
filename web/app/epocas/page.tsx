import type { Metadata } from "next";
import Link from "next/link";
import { HistorySearch } from "@/app/components/HistorySearch";
import { MiniRadar } from "@/app/components/MiniRadar";
import { PercentileLegend } from "@/app/components/PercentileBars";
import { RadarChart } from "@/app/components/RadarChart";
import { Reveal } from "@/app/components/Reveal";
import { competitionColor, seasonDisplay } from "@/lib/format";
import { HISTORY_METRICS, normalizedName } from "@/lib/history";
import {
  bestSeason,
  eraTwins,
  latestYear,
  LINE_LABELS,
  loadProfiles,
  pickSeason,
  pickValue,
  seasonKey,
  seasonScore,
  seasonsOf,
  type Era,
  type Profile,
} from "@/lib/profiles";

const DEFAULT_METADATA: Metadata = {
  title: "Gemelos de época · El Regista",
  description:
    "¿Quién juega hoy como el Messi de 2015? Las temporadas más parecidas desde 2014 en las 5 grandes ligas, por percentiles de Understat.",
};

/** A shared link shows the season and its closest twin as an image. */
export async function generateMetadata(props: PageProps<"/epocas">): Promise<Metadata> {
  const searchParams = await props.searchParams;
  const id = Number(param(searchParams.j));
  if (!id) return DEFAULT_METADATA;
  const profiles = await loadProfiles();
  const target = pickSeason(`${id}:${param(searchParams.s) ?? ""}`, profiles)?.profile;
  if (!target) return DEFAULT_METADATA;
  const era = eraFor(target, latestYear(profiles), param(searchParams.en));
  const [twin] = eraTwins(target, profiles, era, 1);
  const card = `/epocas/carta?a=${pickValue(target)}${twin ? `&b=${pickValue(twin.profile)}` : ""}`;
  return {
    title: twin
      ? `${target.name} ${seasonDisplay(String(target.year))} ≈ ${twin.profile.name} ${seasonDisplay(String(twin.profile.year))} · El Regista`
      : DEFAULT_METADATA.title,
    description: DEFAULT_METADATA.description,
    openGraph: { images: [card] },
    twitter: { card: "summary_large_image", images: [card] },
  };
}

function eraFor(target: Profile, latest: number, asked: string | undefined): Era {
  return asked === "hoy" || asked === "antes" ? asked : target.year === latest ? "antes" : "hoy";
}

// Starting points, looked up by name in the data (never by a hard-coded id).
const EXAMPLES: [string, number][] = [
  ["Lionel Messi", 2015],
  ["N'Golo Kanté", 2015],
  ["Mohamed Salah", 2017],
  ["Kevin De Bruyne", 2019],
  ["Robert Lewandowski", 2020],
  ["Toni Kroos", 2016],
];

function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function href(id: number, season: Profile | string, era?: Era): string {
  const key = typeof season === "string" ? season : seasonKey(season);
  return `/epocas?j=${id}&s=${key}${era ? `&en=${era}` : ""}`;
}

function seasonName(profile: Profile): string {
  return `${profile.competition} ${seasonDisplay(String(profile.year))}`;
}

export default async function ErasPage(props: PageProps<"/epocas">) {
  const searchParams = await props.searchParams;
  const profiles = await loadProfiles();
  const latest = latestYear(profiles);
  const id = Number(param(searchParams.j));
  const seasons = id ? seasonsOf(id, profiles) : [];
  const target = seasons.find((season) => seasonKey(season) === param(searchParams.s)) ?? bestSeason(seasons);

  return (
    <div className="flex flex-col gap-10">
      <header className="flex flex-col gap-3">
        <h1 className="font-display text-5xl leading-[0.92] sm:text-6xl">Gemelos de época</h1>
        <p className="max-w-2xl text-sm text-muted sm:text-base">
          Elige una temporada de cualquier jugador de las 5 grandes desde 2014 y mira quién juega igual en la{" "}
          {seasonDisplay(String(latest))} o en otra época. Mismo puesto, percentiles de Understat frente a los de su liga y
          temporada. También puedes enfrentar dos temporadas en el{" "}
          <Link href="/epocas/duelo" className="font-semibold text-ink underline decoration-line underline-offset-4 hover:text-brand">
            cara a cara histórico
          </Link>
          .
        </p>
        <div className="mt-2 max-w-2xl">
          <HistorySearch placeholder="Busca un jugador: Messi, Kanté, Iniesta..." />
        </div>
      </header>

      {target ? (
        <Twins target={target} seasons={seasons} profiles={profiles} latest={latest} era={param(searchParams.en)} />
      ) : (
        <Examples profiles={profiles} />
      )}
    </div>
  );
}

function Examples({ profiles }: { profiles: Profile[] }) {
  const found = EXAMPLES.flatMap(([name, year]) => {
    const match = profiles.find((profile) => profile.year === year && normalizedName(profile.name) === normalizedName(name));
    return match ? [match] : [];
  });
  if (found.length === 0) return null;
  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-heading text-2xl tracking-tight">Para empezar</h2>
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {found.map((profile) => (
          <li key={profile.id}>
            <Link href={href(profile.id, profile)} className="glass glass-hover flex flex-col rounded-lg p-4">
              <span className="font-heading text-xl">{profile.name}</span>
              <span className="text-sm text-muted">
                {profile.team} · {seasonName(profile)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Twins({
  target,
  seasons,
  profiles,
  latest,
  era: asked,
}: {
  target: Profile;
  seasons: Profile[];
  profiles: Profile[];
  latest: number;
  era: string | undefined;
}) {
  const era = eraFor(target, latest, asked);
  const twins = eraTwins(target, profiles, era);
  const best = bestSeason(seasons);
  const accent = competitionColor(target.competition);
  const ficha = `/historico/ficha?nombre=${encodeURIComponent(target.name)}&liga=${encodeURIComponent(target.competition)}&anio=${target.year}&j=${target.id}&s=${seasonKey(target)}`;

  return (
    <>
      <Reveal>
        <section className="glass grid grid-cols-1 gap-8 rounded-lg p-6 lg:grid-cols-2">
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="font-display text-4xl leading-none sm:text-5xl">{target.name}</h2>
              <p className="mt-2 text-sm text-muted">
                {target.team} · {seasonName(target)} · {target.minutes.toLocaleString("es-ES")}&apos; ·{" "}
                {LINE_LABELS[target.line].toLowerCase()}
              </p>
            </div>
            <p className="text-sm">
              Nota de la temporada <span className="font-display text-3xl tabular-nums">{seasonScore(target)}</span>
              <span className="text-muted"> (media de sus percentiles)</span>
              {best && best !== target && (
                <>
                  {" · "}
                  <Link href={href(best.id, best)} className="font-semibold underline decoration-line underline-offset-4 hover:text-brand">
                    su mejor: {seasonName(best)}
                  </Link>
                </>
              )}
            </p>
            {seasons.length > 1 && (
              <nav aria-label="Temporadas" className="flex flex-wrap gap-1.5">
                {seasons.map((season) => (
                  <Link
                    key={seasonKey(season)}
                    href={href(season.id, season)}
                    aria-current={season === target ? "page" : undefined}
                    className={`rounded-full px-3 py-1 text-sm ${season === target ? "bg-ink text-bg" : "border border-line text-muted hover:text-ink"}`}
                  >
                    {seasonDisplay(String(season.year))}
                  </Link>
                ))}
              </nav>
            )}
            <div className="flex flex-wrap gap-x-6 gap-y-2">
              <Link href={ficha} className="font-semibold text-brand hover:underline">
                Ver su ficha →
              </Link>
              {twins[0] && (
                <Link
                  href={`/epocas/duelo?a=${pickValue(target)}&b=${pickValue(twins[0].profile)}`}
                  className="font-semibold text-brand hover:underline"
                >
                  Cara a cara con {twins[0].profile.name} →
                </Link>
              )}
            </div>
          </div>
          <div>
            <RadarChart axes={HISTORY_METRICS} series={[{ name: target.name, color: accent, values: target.percentiles }]} />
            <PercentileLegend />
          </div>
        </section>
      </Reveal>

      <section className="flex flex-col gap-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h2 className="font-heading text-2xl tracking-tight">
            {era === "hoy" ? `Quién juega así en la ${seasonDisplay(String(latest))}` : "Quién jugó así antes"}
          </h2>
          <nav aria-label="Época" className="flex gap-1.5">
            {(["hoy", "antes"] as const).map((option) => (
              <Link
                key={option}
                href={href(target.id, target, option)}
                aria-current={option === era ? "page" : undefined}
                className={`rounded-lg px-4 py-2 text-sm font-semibold ${option === era ? "bg-ink text-bg" : "glass glass-hover"}`}
              >
                {option === "hoy" ? seasonDisplay(String(latest)) : `2014 a ${seasonDisplay(String(latest - 1))}`}
              </Link>
            ))}
          </nav>
        </div>
        {twins.length === 0 ? (
          <p className="glass rounded-lg p-8 text-center text-sm text-muted">No hay temporadas comparables.</p>
        ) : (
          <ol className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {twins.map(({ profile, similarity }, index) => (
              <li key={profile.id}>
                <Link href={href(profile.id, profile)} className="glass glass-hover flex items-center gap-4 rounded-lg p-3">
                  <span className="w-6 shrink-0 text-right font-heading text-base tabular-nums text-muted">{index + 1}</span>
                  <MiniRadar target={target.percentiles} twin={profile.percentiles} />
                  <span className="flex min-w-0 flex-1 flex-col">
                    <span className="truncate font-heading text-lg">{profile.name}</span>
                    <span className="truncate text-sm text-muted">{profile.team}</span>
                    <span className="truncate text-sm text-muted">{seasonName(profile)}</span>
                  </span>
                  <span className="shrink-0 text-right">
                    <span className="block font-display text-3xl tabular-nums">{similarity}%</span>
                    <span className="text-xs text-muted">parecido</span>
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        )}
        <p className="text-xs text-muted">
          Gris: {target.name} en la {seasonDisplay(String(target.year))}. Azul: el parecido. Solo temporadas de 900 minutos o
          más; las métricas de Understat miden el ataque y la creación, no la defensa.
        </p>
      </section>
    </>
  );
}
