import type { Metadata } from "next";
import Link from "next/link";
import { HistorySearch } from "@/app/components/HistorySearch";
import { RadarChart } from "@/app/components/RadarChart";
import { Reveal } from "@/app/components/Reveal";
import { seasonDisplay } from "@/lib/format";
import { HISTORY_METRICS } from "@/lib/history";
import { METRICS } from "@/lib/metrics";
import {
  LINE_LABELS,
  loadProfiles,
  pickSeason,
  pickValue,
  seasonName,
  seasonScore,
  similarity,
  type Profile,
} from "@/lib/profiles";

const COLOR_A = "#c93c17";
const COLOR_B = "#2350d8";

type Props = PageProps<"/epocas/duelo">;

function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const searchParams = await props.searchParams;
  const profiles = await loadProfiles();
  const a = pickSeason(param(searchParams.a), profiles)?.profile;
  const b = pickSeason(param(searchParams.b), profiles)?.profile;
  if (!a || !b) {
    return {
      title: "Cara a cara histórico · El Regista",
      description: "Dos temporadas cualesquiera de las 5 grandes desde 2014, frente a frente.",
    };
  }
  const card = `/epocas/carta?a=${pickValue(a)}&b=${pickValue(b)}`;
  return {
    title: `${a.name} ${seasonDisplay(String(a.year))} contra ${b.name} ${seasonDisplay(String(b.year))} · El Regista`,
    description: `Cara a cara de ${a.name} (${seasonName(a)}) y ${b.name} (${seasonName(b)}) con las métricas de Understat.`,
    openGraph: { images: [card] },
    twitter: { card: "summary_large_image", images: [card] },
  };
}

function per90(profile: Profile, key: (typeof HISTORY_METRICS)[number]): number {
  return (profile.totals[key] * 90) / profile.minutes;
}

export default async function HistoryDuelPage(props: Props) {
  const searchParams = await props.searchParams;
  const profiles = await loadProfiles();
  const a = pickSeason(param(searchParams.a), profiles);
  const b = pickSeason(param(searchParams.b), profiles);
  const href = (side: "a" | "b", value: string) => {
    const query = new URLSearchParams();
    const other = side === "a" ? b : a;
    query.set(side, value);
    if (other) query.set(side === "a" ? "b" : "a", pickValue(other.profile));
    return `/epocas/duelo?${query.toString().replaceAll("%3A", ":").replace("%7Bid%7D", "{id}")}`;
  };

  return (
    <div className="flex flex-col gap-10">
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-5xl leading-[0.92] sm:text-6xl">Cara a cara histórico</h1>
        <p className="max-w-2xl text-sm text-muted sm:text-base">
          Dos temporadas cualesquiera de las 5 grandes desde 2014, aunque ya no jueguen. Cada una se mide frente a los de su
          puesto en su liga y temporada.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {([
          ["a", a, COLOR_A],
          ["b", b, COLOR_B],
        ] as const).map(([side, pick, color]) => (
          <div key={side} className="flex flex-col gap-3">
            <HistorySearch
              placeholder={pick ? `Cambiar a ${pick.profile.name}` : side === "a" ? "Primer jugador" : "Segundo jugador"}
              href={href(side, "{id}")}
              accent={color}
            />
            {pick && (
              <div className="flex flex-col gap-2">
                <p className="font-heading text-2xl" style={{ color }}>
                  {pick.profile.name}
                </p>
                <p className="text-sm text-muted">
                  {pick.profile.team} · {seasonName(pick.profile)} · {pick.profile.minutes.toLocaleString("es-ES")}&apos; ·{" "}
                  {LINE_LABELS[pick.profile.line].toLowerCase()}
                </p>
                {pick.seasons.length > 1 && (
                  <nav aria-label="Temporada" className="flex flex-wrap gap-1.5">
                    {pick.seasons.map((season) => (
                      <Link
                        key={pickValue(season)}
                        href={href(side, pickValue(season))}
                        aria-current={season === pick.profile ? "page" : undefined}
                        className={`rounded-full px-3 py-1 text-sm ${season === pick.profile ? "bg-ink text-bg" : "border border-line text-muted hover:text-ink"}`}
                      >
                        {seasonDisplay(String(season.year))}
                      </Link>
                    ))}
                  </nav>
                )}
              </div>
            )}
          </div>
        ))}
      </section>

      {a && b ? <Duel a={a.profile} b={b.profile} /> : null}
    </div>
  );
}

function Duel({ a, b }: { a: Profile; b: Profile }) {
  const wins = HISTORY_METRICS.reduce(
    (count, key) => {
      const gap = per90(a, key) - per90(b, key);
      if (Math.abs(gap) < 1e-9) return count;
      return gap > 0 ? { ...count, a: count.a + 1 } : { ...count, b: count.b + 1 };
    },
    { a: 0, b: 0 },
  );

  return (
    <>
      <Reveal>
        <section className="glass grid grid-cols-1 items-center gap-8 rounded-lg p-6 lg:grid-cols-2">
          <div className="flex flex-col gap-4">
            <div className="flex items-baseline gap-6">
              <span className="font-display text-6xl tabular-nums">{similarity(a, b)}%</span>
              <span className="text-sm text-muted">de parecido en su forma de jugar</span>
            </div>
            <p className="text-lg">
              Por 90 minutos gana{" "}
              <strong style={{ color: wins.a >= wins.b ? COLOR_A : COLOR_B }}>{wins.a >= wins.b ? a.name : b.name}</strong> en{" "}
              {Math.max(wins.a, wins.b)} de {HISTORY_METRICS.length} métricas. Nota de la temporada:{" "}
              <span style={{ color: COLOR_A }}>{seasonScore(a)}</span> frente a{" "}
              <span style={{ color: COLOR_B }}>{seasonScore(b)}</span>.
            </p>
            {a.line !== b.line && (
              <p className="text-sm text-muted">
                Juegan en líneas distintas: cada percentil es frente a los de su propio puesto.
              </p>
            )}
          </div>
          <div className="flex flex-col gap-2">
            <RadarChart
              axes={HISTORY_METRICS}
              series={[
                { name: `${a.name} ${seasonDisplay(String(a.year))}`, color: COLOR_A, values: a.percentiles },
                { name: `${b.name} ${seasonDisplay(String(b.year))}`, color: COLOR_B, values: b.percentiles },
              ]}
            />
            <p className="flex flex-wrap justify-center gap-x-5 text-sm font-semibold">
              <span style={{ color: COLOR_A }}>
                {a.name} {seasonDisplay(String(a.year))}
              </span>
              <span style={{ color: COLOR_B }}>
                {b.name} {seasonDisplay(String(b.year))}
              </span>
            </p>
          </div>
        </section>
      </Reveal>

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-2xl tracking-tight">Métrica a métrica</h2>
        <table className="w-full text-sm">
          <thead className="text-left text-muted">
            <tr className="border-b border-line">
              <th className="py-2 font-semibold">Métrica</th>
              <th className="py-2 text-right font-semibold" style={{ color: COLOR_A }}>
                {a.name}
              </th>
              <th className="py-2 text-right font-semibold" style={{ color: COLOR_B }}>
                {b.name}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {HISTORY_METRICS.map((key) => {
              const left = per90(a, key);
              const right = per90(b, key);
              const cell = (profile: Profile, mine: number, theirs: number, color: string) => (
                <td className="py-2.5 text-right tabular-nums">
                  <span className={mine > theirs ? "font-bold" : "text-muted"} style={mine > theirs ? { color } : undefined}>
                    {mine.toFixed(2)}
                  </span>
                  <span className="block text-xs text-muted">
                    {profile.totals[key].toLocaleString("es-ES", { maximumFractionDigits: 1 })} en total · percentil {profile.percentiles[key]}
                  </span>
                </td>
              );
              return (
                <tr key={key}>
                  <td className="py-2.5">{METRICS[key].label} por 90&apos;</td>
                  {cell(a, left, right, COLOR_A)}
                  {cell(b, right, left, COLOR_B)}
                </tr>
              );
            })}
            <tr>
              <td className="py-2.5">Minutos</td>
              <td className="py-2.5 text-right tabular-nums">{a.minutes.toLocaleString("es-ES")}</td>
              <td className="py-2.5 text-right tabular-nums">{b.minutes.toLocaleString("es-ES")}</td>
            </tr>
          </tbody>
        </table>
        <p className="text-xs text-muted">Datos de Understat: miden el ataque y la creación, no la defensa.</p>
      </section>
    </>
  );
}
