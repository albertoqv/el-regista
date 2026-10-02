import Link from "next/link";
import type { Forecast } from "@/lib/api";

const RESULT_LABEL: Record<string, string> = { w: "V", d: "E", l: "D" };
const RESULT_COLOR: Record<string, string> = {
  w: "bg-grass/85 text-bg",
  d: "bg-ink/25 text-ink",
  l: "bg-rose-500/80 text-white",
};

/** Last results, latest first: V (victoria), E (empate), D (derrota). */
export function FormPills({ form, size = "sm" }: { form: string[]; size?: "sm" | "md" }) {
  const box = size === "md" ? "h-6 w-6 text-xs" : "h-5 w-5 text-[10px]";
  return (
    <span className="inline-flex flex-wrap gap-1" title="Últimos resultados, el más reciente primero">
      {form.map((result, index) => (
        <span
          key={index}
          className={`inline-flex items-center justify-center rounded-md font-bold ${box} ${RESULT_COLOR[result] ?? "bg-ink/10"}`}
        >
          {RESULT_LABEL[result] ?? "?"}
        </span>
      ))}
    </span>
  );
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function ProbabilityBar({
  home,
  draw,
  away,
}: {
  home: number;
  draw: number;
  away: number;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex h-3 overflow-hidden rounded-full">
        <div className="bg-side-a" style={{ width: percent(home) }} />
        <div className="bg-ink/30" style={{ width: percent(draw) }} />
        <div className="bg-side-b" style={{ width: percent(away) }} />
      </div>
      <div className="flex justify-between text-xs font-semibold tabular-nums">
        <span className="text-side-a">1 · {percent(home)}</span>
        <span className="text-ink/70">X · {percent(draw)}</span>
        <span className="text-side-b">{percent(away)} · 2</span>
      </div>
    </div>
  );
}

/** How a scout would say it, from the model's probabilities. */
function verdict(forecast: Forecast): string {
  const options = [
    { label: `gana ${forecast.home_team}`, p: forecast.home_win },
    { label: "empate", p: forecast.draw },
    { label: `gana ${forecast.away_team}`, p: forecast.away_win },
  ].sort((a, b) => b.p - a.p);
  const [best, second] = options;
  if (best.p >= 0.6) return `Claro favorito: ${best.label}`;
  if (best.p - second.p < 0.07) return "Partido muy abierto";
  return `Ligera ventaja: ${best.label}`;
}

function teamHref(team: string, competition: string): string {
  return `/equipos/${encodeURIComponent(team)}?liga=${encodeURIComponent(competition)}`;
}

/** Understat kick-offs are UTC without a zone suffix. */
export function kickoffDate(iso: string): Date {
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
}

export function ForecastCard({ forecast }: { forecast: Forecast }) {
  const kickoff = kickoffDate(forecast.kickoff);
  return (
    <article className="glass flex flex-col gap-4 rounded-lg p-5">
      <div className="flex items-center justify-between text-xs text-muted">
        <span className="flex items-center gap-1.5">
          {forecast.competition}
        </span>
        <span>
          {kickoff.toLocaleDateString("es-ES", { weekday: "short", day: "numeric", month: "short", timeZone: "Europe/Madrid" })}{" "}
          · {kickoff.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Madrid" })} h
        </span>
      </div>

      <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3">
        <Link href={teamHref(forecast.home_team, forecast.competition)} className="flex min-w-0 flex-col gap-1 hover:underline">
          <span className="font-heading text-base leading-tight">{forecast.home_team}</span>
          <FormPills form={forecast.home_form.slice(0, 3)} />
        </Link>
        <div className="flex flex-col items-center">
          <span className="whitespace-nowrap font-display text-xl font-bold tabular-nums">
            {forecast.expected_home.toFixed(1)} – {forecast.expected_away.toFixed(1)}
          </span>
          <span className="text-xs text-muted">goles esperados</span>
        </div>
        <Link
          href={teamHref(forecast.away_team, forecast.competition)}
          className="flex min-w-0 flex-col items-end gap-1 text-right hover:underline"
        >
          <span className="font-heading text-base leading-tight">{forecast.away_team}</span>
          <span className="flex justify-end">
            <FormPills form={forecast.away_form.slice(0, 3)} />
          </span>
        </Link>
      </div>

      <ProbabilityBar home={forecast.home_win} draw={forecast.draw} away={forecast.away_win} />

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="font-hand text-lg text-[#c93c17]">{verdict(forecast)}</span>
        <span className="flex flex-wrap gap-1.5">
          {forecast.scorelines.slice(0, 3).map((score) => (
            <span key={`${score.home}-${score.away}`} className="rounded-md bg-ink/5 px-2 py-1 tabular-nums">
              {score.home}-{score.away} <span className="text-muted">{percent(score.probability)}</span>
            </span>
          ))}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <span className="rounded-xl bg-ink/5 px-3 py-2">
          Más de 2,5 goles <strong className="float-right tabular-nums">{percent(forecast.over_2_5)}</strong>
        </span>
        <span className="rounded-xl bg-ink/5 px-3 py-2">
          Marcan ambos <strong className="float-right tabular-nums">{percent(forecast.both_teams_score)}</strong>
        </span>
      </div>
      <Link
        href={`/predicciones/${forecast.match_id}`}
        className="mt-auto rounded-full bg-ink px-4 py-2 text-center text-xs font-bold text-bg transition hover:bg-ink/85"
      >
        Ver análisis completo
      </Link>
    </article>
  );
}
