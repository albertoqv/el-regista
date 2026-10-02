import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { kickoffDate, ProbabilityBar } from "@/app/components/Forecast";
import { Reveal } from "@/app/components/motion";
import { PlayerMarketsTable } from "@/app/components/PlayerMarketsTable";
import { ScoutNote, Sticker } from "@/app/components/ScoutNote";
import {
  ApiError,
  getMatchInsights,
  getPlayerMarkets,
  type MatchInsights,
  type MatchLine,
  type Outcome,
  type PlayerMarkets,
  type StatForecast,
} from "@/lib/api";
import { competitionColor } from "@/lib/format";

export async function generateMetadata(props: PageProps<"/predicciones/[match]">): Promise<Metadata> {
  const { match } = await props.params;
  const insights = await getMatchInsights(Number(match)).catch(() => null);
  return {
    title: insights ? `${insights.home_team} - ${insights.away_team} · Pronóstico` : "Pronóstico",
  };
}

const STAT_LABELS: Record<string, { title: string; unit: string }> = {
  corners: { title: "Córners", unit: "córners" },
  yellows: { title: "Tarjetas amarillas", unit: "amarillas" },
  fouls: { title: "Faltas", unit: "faltas" },
  shots: { title: "Tiros", unit: "tiros" },
  shots_on_target: { title: "Tiros a puerta", unit: "a puerta" },
};

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function decimal(value: number): string {
  return value.toFixed(1).replace(".", ",");
}

function OutcomeRow({ label, outcome, note }: { label: string; outcome: Outcome; note?: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="flex justify-between text-xs font-semibold text-muted">
        {label}
        {note && <span className="normal-case tracking-normal">{note}</span>}
      </span>
      <ProbabilityBar home={outcome.home_win} draw={outcome.draw} away={outcome.away_win} />
    </div>
  );
}

function Histogram({ values, highlight }: { values: number[]; highlight: number }) {
  const shown = values.slice(0, Math.max(values.length, 1));
  const max = Math.max(...shown, 0.001);
  return (
    <div className="flex h-16 items-end gap-[2px]" aria-hidden="true">
      {shown.map((value, index) => (
        <div
          key={index}
          className="flex-1 rounded-t-sm"
          style={{
            height: `${(value / max) * 100}%`,
            background: index > highlight ? "#2350d8" : "rgba(22,23,27,0.18)",
          }}
          title={`${index}: ${percent(value)}`}
        />
      ))}
    </div>
  );
}

function StatCard({ stat, home, away }: { stat: StatForecast; home: string; away: string }) {
  const label = STAT_LABELS[stat.stat] ?? { title: stat.stat, unit: "" };
  const main = stat.over[Math.floor(stat.over.length / 2)];
  const leader =
    stat.home_more > stat.away_more
      ? { team: home, p: stat.home_more }
      : { team: away, p: stat.away_more };
  return (
    <div className="glass flex flex-col gap-3 rounded-lg p-5">
      <div className="flex items-baseline justify-between">
        <h3 className="font-heading text-lg">{label.title}</h3>
        <span className="font-display text-2xl font-bold tabular-nums">{decimal(stat.expected_total)}</span>
      </div>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 text-sm">
        <span className="font-display text-xl font-bold tabular-nums text-side-a">{decimal(stat.expected_home)}</span>
        <span className="text-xs text-muted">esperados</span>
        <span className="text-right font-display text-xl font-bold tabular-nums text-side-b">
          {decimal(stat.expected_away)}
        </span>
      </div>
      <p className="text-sm">
        <span className="text-muted">Más {label.unit}: </span>
        <strong>{leader.team}</strong> <span className="text-muted">({percent(leader.p)})</span>
      </p>
      {main && <Histogram values={stat.distribution} highlight={main.line} />}
      <div className="flex flex-wrap gap-1.5 text-xs">
        {stat.over.map((line) => (
          <span key={line.line} className="rounded-md bg-ink/5 px-2 py-1 tabular-nums">
            +{String(line.line).replace(".", ",")} <strong>{percent(line.over)}</strong>
          </span>
        ))}
      </div>
    </div>
  );
}

function MatchTable({ title, rows }: { title: string; rows: MatchLine[] }) {
  if (rows.length === 0) return null;
  return (
    <div className="glass overflow-x-auto rounded-lg p-4">
      <h3 className="mb-2 font-heading text-lg">{title}</h3>
      <table className="w-full min-w-[460px] text-sm">
        <thead>
          <tr className="text-left text-xs text-muted">
            <th className="py-1">Fecha</th>
            <th>Partido</th>
            <th className="text-center">Res.</th>
            <th className="text-center">Córners</th>
            <th className="text-center">Amarillas</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.played_on}-${row.home_team}`} className="border-t border-line/60">
              <td className="py-1.5 text-xs text-muted">
                {new Date(row.played_on).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "2-digit" })}
              </td>
              <td className="truncate">
                {row.home_team} – {row.away_team}
              </td>
              <td className="text-center font-display font-bold tabular-nums">
                {row.home_goals}-{row.away_goals}
              </td>
              <td className="text-center tabular-nums text-muted">
                {row.home_corners ?? "–"}-{row.away_corners ?? "–"}
              </td>
              <td className="text-center tabular-nums text-muted">
                {row.home_yellows ?? "–"}-{row.away_yellows ?? "–"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default async function MatchPage(props: PageProps<"/predicciones/[match]">) {
  const { match } = await props.params;
  const matchId = Number(match);
  let insights: MatchInsights;
  try {
    insights = await getMatchInsights(matchId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
  const markets = await getPlayerMarkets(matchId).catch((): PlayerMarkets | null => null);
  const kickoff = kickoffDate(insights.kickoff);
  const color = competitionColor(insights.competition);

  return (
    <div className="flex flex-col gap-8">
      <Reveal>
        <Link href="/predicciones" className="text-sm text-muted hover:text-ink">
          ← Predicciones
        </Link>
        <p className="mt-3 flex items-center gap-2 text-xs font-semibold" style={{ color }}>
          {insights.competition} ·{" "}
          {kickoff.toLocaleString("es-ES", {
            weekday: "long",
            day: "numeric",
            month: "long",
            hour: "2-digit",
            minute: "2-digit",
            timeZone: "Europe/Madrid",
          })}
        </p>
        <h1 className="mt-1 grid grid-cols-[1fr_auto_1fr] items-center gap-4 font-display text-3xl font-bold tracking-tight sm:text-5xl">
          <span>{insights.home_team}</span>
          <span className="whitespace-nowrap text-center text-2xl text-muted sm:text-4xl">
            {decimal(insights.expected_home)} – {decimal(insights.expected_away)}
          </span>
          <span className="text-right">{insights.away_team}</span>
        </h1>
        <p className="mt-1 text-center text-xs text-muted">goles esperados</p>
      </Reveal>

      <Reveal>
        <section className="glass grid grid-cols-1 gap-5 rounded-lg p-5 sm:p-6 lg:grid-cols-2">
          <div className="flex flex-col gap-4">
            <h2 className="font-heading text-2xl tracking-tight">Resultado</h2>
            {insights.market && (
              <OutcomeRow
                label="Casas de apuestas"
                outcome={insights.market}
                note="la referencia más fiable en 1X2"
              />
            )}
            <OutcomeRow
              label="Nuestro modelo"
              outcome={insights.result}
              note={insights.market ? "opinión independiente" : undefined}
            />
            <OutcomeRow label="Al descanso" outcome={insights.half_time} />
          </div>
          <div className="flex flex-col gap-4">
            <h2 className="font-heading text-2xl tracking-tight">Goles</h2>
            <div className="grid grid-cols-5 gap-2 text-center">
              {insights.goals_over.map((line) => (
                <div key={line.line} className="rounded-lg bg-ink/5 p-2">
                  <span className="block text-xs text-muted">+{String(line.line).replace(".", ",")}</span>
                  <span className="font-display text-lg font-bold tabular-nums">{percent(line.over)}</span>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-lg bg-ink/5 p-2">
                <span className="block text-muted">Marcan ambos</span>
                <strong className="font-heading text-lg">{percent(insights.both_teams_score)}</strong>
              </div>
              <div className="rounded-lg bg-ink/5 p-2">
                <span className="block text-muted">{insights.home_team} a cero</span>
                <strong className="font-heading text-lg">{percent(insights.home_clean_sheet)}</strong>
              </div>
              <div className="rounded-lg bg-ink/5 p-2">
                <span className="block text-muted">{insights.away_team} a cero</span>
                <strong className="font-heading text-lg">{percent(insights.away_clean_sheet)}</strong>
              </div>
            </div>
            <div>
              <span className="text-xs font-semibold text-muted">Marcadores más probables</span>
              <div className="mt-2 flex flex-wrap gap-2">
                {insights.scorelines.map((score, index) => (
                  <span key={`${score.home}-${score.away}`} className="rounded-xl bg-ink/5 px-3 py-2 font-display font-bold tabular-nums">
                    {score.home}-{score.away}{" "}
                    <span className="text-xs font-normal text-muted">{percent(score.probability)}</span>
                    {index === 0 && <Sticker tone="yellow" rotate={-4} className="ml-2">top</Sticker>}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>
      </Reveal>

      {insights.stats.length > 0 && (
        <section className="flex flex-col gap-4">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <h2 className="font-heading text-2xl tracking-tight">Estadísticas del partido</h2>
            {insights.referee && (
              <span className="glass rounded-lg px-4 py-2 text-sm">
                <ScoutNote rotate={-2} className="text-base">árbitro:</ScoutNote> <strong>{insights.referee.name}</strong>{" "}
                <span className="text-muted">
                  · {decimal(insights.referee.yellows_per_match)} amarillas/partido en {insights.referee.matches} partidos
                  {insights.referee.multiplier > 1.05 ? " (tarjetero)" : insights.referee.multiplier < 0.95 ? " (permisivo)" : ""}
                </span>
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {insights.stats.map((stat) => (
              <StatCard key={stat.stat} stat={stat} home={insights.home_team} away={insights.away_team} />
            ))}
          </div>
        </section>
      )}

      {markets && (markets.home.length > 0 || markets.away.length > 0) && (
        <Reveal>
          <PlayerMarketsTable markets={markets} />
        </Reveal>
      )}

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <MatchTable title="Cara a cara" rows={insights.head_to_head} />
        <MatchTable title={`Últimos de ${insights.home_team}`} rows={insights.home_recent} />
        <MatchTable title={`Últimos de ${insights.away_team}`} rows={insights.away_recent} />
      </section>

      <p className="text-center text-xs text-muted">
        Probabilidades estadísticas, no certezas. No incluyen lesiones ni alineaciones confirmadas.{" "}
        <Link href="/como-funciona#predicciones" className="text-brand-2 hover:underline">
          Cómo se calculan
        </Link>
      </p>
    </div>
  );
}
