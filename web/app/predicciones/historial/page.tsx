import type { Metadata } from "next";
import { PageHeader } from "@/app/components/PageHeader";
import { PHOTOS } from "@/lib/photos";
import Link from "next/link";
import { kickoffDate } from "@/app/components/Forecast";
import { getTrackRecord, type RecordTotals, type ScoredPick, type WeekRecord } from "@/lib/api";
import { currentSeasonStartYear, seasonDisplay } from "@/lib/format";

export const metadata: Metadata = {
  title: "Historial de aciertos · El Regista",
  description:
    "Nuestras predicciones guardadas antes de cada partido, comparadas con el resultado real. Sin maquillaje.",
};

function decimal(value: number): string {
  return value.toLocaleString("es-ES", { minimumFractionDigits: 3, maximumFractionDigits: 3 });
}

function percent(part: number, total: number): string {
  return total ? `${Math.round((part / total) * 100)}%` : "—";
}

function weekLabel(iso: string): string {
  return new Date(`${iso}T12:00:00Z`).toLocaleDateString("es-ES", { day: "numeric", month: "short" });
}

function Kpi({ label, value, hint, tone }: { label: string; value: string; hint?: string; tone?: string }) {
  return (
    <div className="glass rounded-lg p-4">
      <p className="text-xs font-semibold text-muted">{label}</p>
      <p className="mt-1 font-display text-2xl font-bold tabular-nums sm:text-3xl" style={tone ? { color: tone } : undefined}>
        {value}
      </p>
      {hint ? <p className="mt-0.5 text-xs text-muted">{hint}</p> : null}
    </div>
  );
}

function Totals({ totals, withMarket }: { totals: RecordTotals; withMarket: boolean }) {
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Kpi label="Partidos" value={totals.matches.toLocaleString("es-ES")} />
      <Kpi
        label="Acierto 1X2"
        value={percent(totals.hits, totals.matches)}
        hint={`${totals.hits} de ${totals.matches} · al azar ~33%`}
        tone="#1f8a4c"
      />
      <Kpi
        label="Con 60% o más"
        value={percent(totals.confident_hits, totals.confident)}
        hint={`${totals.confident_hits} de ${totals.confident} picks seguros`}
        tone="#c93c17"
      />
      {withMarket && totals.market_brier !== null ? (
        <Kpi
          label="Brier: modelo / casas"
          value={`${decimal(totals.brier)} / ${decimal(totals.market_brier)}`}
          hint="Menos es mejor"
        />
      ) : (
        <Kpi label="Brier" value={totals.matches ? decimal(totals.brier) : "—"} hint="Menos es mejor · azar 0,667" />
      )}
    </div>
  );
}

function WeeklyChart({ weeks }: { weeks: WeekRecord[] }) {
  if (weeks.length === 0) return null;
  return (
    <div className="glass rounded-lg p-4 sm:p-5">
      <div className="flex flex-col gap-0.5 sm:flex-row sm:items-baseline sm:justify-between sm:gap-3">
        <h3 className="font-heading text-lg">Semana a semana</h3>
        <span className="text-xs text-muted">% de 1X2 acertados · línea: azar (33%)</span>
      </div>
      <div className="no-scrollbar mt-4 overflow-x-auto">
        <div className="relative flex h-44 min-w-full items-end gap-1.5" style={{ width: `max(100%, ${weeks.length * 44}px)` }}>
          <span className="pointer-events-none absolute inset-x-0 border-t border-dashed border-ink/20" style={{ bottom: "33%" }} />
          {weeks.map((week) => {
            const rate = week.matches ? week.hits / week.matches : 0;
            return (
              <div key={week.week_start} className="flex h-full min-w-[38px] flex-1 flex-col items-center justify-end gap-1">
                <span className="text-xs font-semibold tabular-nums">{Math.round(rate * 100)}%</span>
                <div
                  className="w-full rounded-t-lg"
                  style={{
                    height: `${Math.max(rate * 100, 2)}%`,
                    background: rate >= 0.5 ? "#c93c17" : rate >= 0.34 ? "#1f8a4c" : "#4d7563",
                  }}
                  title={`${week.hits} de ${week.matches}`}
                />
                <span className="text-xs text-muted">{weekLabel(week.week_start)}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

const OUTCOMES = ["1", "X", "2"] as const;

function PickRow({ pick }: { pick: ScoredPick }) {
  const best = pick.model.indexOf(Math.max(...pick.model));
  const kickoff = kickoffDate(pick.kickoff);
  const pickLabel = best === 0 ? pick.home_team : best === 2 ? pick.away_team : "Empate";
  return (
    <li className="flex items-center gap-3 rounded-lg px-3 py-2.5 odd:bg-ink/[0.02]">
      <span
        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-bold ${pick.model_hit ? "bg-grass/25 text-brand-2" : "bg-red-500/15 text-red-300"}`}
        aria-label={pick.model_hit ? "Acierto" : "Fallo"}
      >
        {pick.model_hit ? "✓" : "✗"}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-semibold">
          {pick.home_team} {pick.home_goals}-{pick.away_goals} {pick.away_team}
        </span>
        <span className="flex items-center gap-1.5 text-xs text-muted">
          {kickoff.toLocaleDateString("es-ES", { day: "numeric", month: "short", timeZone: "Europe/Madrid" })} · dijimos{" "}
          {OUTCOMES[best]} ({pickLabel}) al {Math.round(pick.model[best] * 100)}%
        </span>
      </span>
    </li>
  );
}

export default async function TrackRecordPage() {
  const season = currentSeasonStartYear();
  const record = await getTrackRecord(season).catch(() => null);

  return (
    <div className="flex flex-col gap-10">
      <PageHeader photo={PHOTOS.historial.src} title="Historial de aciertos">Guardado antes del partido. Puntuado después.</PageHeader>

      {record === null ? (
        <p className="glass rounded-lg p-8 text-center text-muted">
          No hemos podido cargar el historial ahora mismo. Vuelve a intentarlo en un minuto.
        </p>
      ) : (
        <>
          <section className="flex flex-col gap-4">
            <div>
              <p className="text-xs font-semibold text-brand-2">En vivo</p>
              <h2 className="font-heading text-2xl tracking-tight sm:text-3xl">Predicciones registradas</h2>
            </div>
            {record.live_total.matches === 0 ? (
              <p className="glass rounded-lg p-6 text-sm text-muted">
                Empezamos esta semana: los primeros resultados llegan tras la próxima jornada.
              </p>
            ) : (
              <>
                <Totals totals={record.live_total} withMarket={record.live_total.market_matches > 0} />
                <WeeklyChart weeks={record.live_weeks} />
                <div className="glass rounded-lg p-3 sm:p-4">
                  <h3 className="px-2 pb-2 font-heading text-lg">Últimos partidos</h3>
                  <ul className="flex flex-col">
                    {record.live_recent.map((pick) => (
                      <PickRow key={pick.match_id} pick={pick} />
                    ))}
                  </ul>
                  {record.pending > 0 ? (
                    <p className="px-2 pt-2 text-xs text-muted">{record.pending} partidos más esperando resultado.</p>
                  ) : null}
                </div>
              </>
            )}
          </section>

          <section className="flex flex-col gap-4">
            <div>
              <p className="text-xs font-semibold text-brand-2">Reconstruido</p>
              <h2 className="font-heading text-2xl tracking-tight sm:text-3xl">
                Temporada {seasonDisplay(record.season_label)}, jornada a jornada
              </h2>
              <p className="mt-1 max-w-2xl text-sm text-muted">Cada partido predicho solo con lo que había pasado antes.</p>
            </div>
            {record.rebuilt_total.matches === 0 ? (
              <p className="glass rounded-lg p-6 text-sm text-muted">
                Aún no hay suficientes partidos jugados esta temporada para puntuar.
              </p>
            ) : (
              <>
                <Totals totals={record.rebuilt_total} withMarket={false} />
                <WeeklyChart weeks={record.rebuilt_weeks} />
              </>
            )}
          </section>

          <Link href="/como-funciona" className="text-sm text-brand-2 hover:underline">
            Cómo se calcula →
          </Link>
        </>
      )}
    </div>
  );
}
