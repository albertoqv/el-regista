import type { Metadata } from "next";
import Link from "next/link";
import { ForecastCard, kickoffDate } from "@/app/components/Forecast";
import { Reveal } from "@/app/components/motion";
import { RoundHighlights } from "@/app/components/RoundHighlights";
import { ScoutNote } from "@/app/components/ScoutNote";
import {
  getBacktest,
  getHighlights,
  getMarketBenchmark,
  getPredictions,
  type Backtest,
  type Forecast,
  type Highlights,
  type MarketBenchmark,
} from "@/lib/api";
import { COMPETITIONS, competitionColor, currentSeasonStartYear, seasonDisplay } from "@/lib/format";

export const metadata: Metadata = {
  title: "Predicciones · El Regista",
  description: "Pronósticos de los próximos partidos de las 5 grandes ligas con un modelo evaluado en público.",
};

// Enough to always reach the next matchday, even after an international break.
const WINDOW_DAYS = 21;

function param(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function dayLabel(iso: string): string {
  return kickoffDate(iso).toLocaleDateString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "Europe/Madrid",
  });
}

function TrustPanel({
  backtest,
  season,
  benchmark,
}: {
  backtest: Backtest;
  season: string;
  benchmark: MarketBenchmark | null;
}) {
  const edge = backtest.accuracy - backtest.baseline_accuracy;
  return (
    <section className="glass grid grid-cols-2 gap-4 rounded-lg p-5 sm:grid-cols-4">
      <div className="col-span-2 sm:col-span-4">
        <h2 className="font-display text-lg font-bold">¿Cuánto acierta el modelo?</h2>
        <p className="text-sm text-muted">
          {backtest.matches.toLocaleString("es-ES")} partidos de la {seasonDisplay(season)}, cada uno predicho solo con lo anterior.{" "}
          <Link href="/como-funciona#predicciones" className="text-brand-2 hover:underline">
            Cómo funciona →
          </Link>
        </p>
      </div>
      <div>
        <span className="block font-display text-3xl font-bold">{Math.round(backtest.accuracy * 100)}%</span>
        <span className="text-xs text-muted">acierta el resultado (1X2)</span>
      </div>
      <div>
        <span className="block font-display text-3xl font-bold text-brand-2">
          +{Math.round(edge * 100)} pts
        </span>
        <span className="text-xs text-muted">sobre apostar siempre por lo más habitual</span>
      </div>
      <div>
        <span className="block font-display text-3xl font-bold">{backtest.brier.toFixed(3)}</span>
        <span className="text-xs text-muted">Brier (menos es mejor; azar ≈ 0,667)</span>
      </div>
      <div>
        <span className="block font-display text-3xl font-bold">
          {Math.round(
            (backtest.calibration.reduce((sum, b) => sum + Math.abs(b.predicted - b.observed) * b.count, 0) /
              Math.max(backtest.calibration.reduce((sum, b) => sum + b.count, 0), 1)) *
              1000,
          ) / 10}
          %
        </span>
        <span className="text-xs text-muted">desvío medio entre lo que dice y lo que pasa</span>
      </div>
      {benchmark && benchmark.matches > 0 && (
        <p className="col-span-2 rounded-lg bg-white/[0.04] p-3 text-sm sm:col-span-4">
          <strong>Frente a las casas de apuestas</strong>: nuestro modelo{" "}
          <strong>{benchmark.model_brier.toFixed(3)}</strong>, cuotas de cierre{" "}
          <strong>{benchmark.market_brier.toFixed(3)}</strong>. En el 1X2 aciertan más las casas; lo
          nuestro es lo que sus cuotas gratuitas no dan: córners, tarjetas y jugadores.
        </p>
      )}
    </section>
  );
}

export default async function PredictionsPage(props: PageProps<"/predicciones">) {
  const searchParams = await props.searchParams;
  const league = param(searchParams.liga);
  const lastSeason = String(currentSeasonStartYear() - 1);
  const [forecasts, backtest, highlights, benchmark] = await Promise.all([
    getPredictions(WINDOW_DAYS, league).catch((): Forecast[] => []),
    getBacktest(lastSeason).catch((): Backtest | null => null),
    league ? Promise.resolve(null) : getHighlights(5).catch((): Highlights | null => null),
    getMarketBenchmark(lastSeason).catch((): MarketBenchmark | null => null),
  ]);

  const byDay = new Map<string, Forecast[]>();
  for (const forecast of forecasts) {
    const day = kickoffDate(forecast.kickoff).toLocaleDateString("sv-SE", { timeZone: "Europe/Madrid" });
    byDay.set(day, [...(byDay.get(day) ?? []), forecast]);
  }

  return (
    <div className="flex flex-col gap-8">
      <Reveal>
        <ScoutNote rotate={-2}>números, no corazonadas</ScoutNote>
        <h1 className="font-display text-4xl font-bold tracking-tight sm:text-5xl">Próximos partidos</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">Probabilidades de cada partido.</p>
      </Reveal>

      {highlights && (
        <Reveal>
          <RoundHighlights highlights={highlights} />
        </Reveal>
      )}

      {backtest && backtest.matches > 0 && (
        <Reveal>
          <TrustPanel backtest={backtest} season={lastSeason} benchmark={benchmark} />
        </Reveal>
      )}

      <div className="no-scrollbar -mx-4 flex gap-2 overflow-x-auto px-4 sm:mx-0 sm:flex-wrap sm:px-0">
        {[undefined, ...COMPETITIONS].map((option) => {
          const active = league === option;
          const color = option ? competitionColor(option) : "#7cc0ff";
          return (
            <Link
              key={option ?? "all"}
              href={option ? `/predicciones?liga=${encodeURIComponent(option)}` : "/predicciones"}
              className="flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition"
              style={{
                borderColor: active ? color : "rgba(255,255,255,0.08)",
                background: active ? `${color}22` : "transparent",
                color: active ? "#fff" : "#8b93a7",
              }}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
              {option ?? "Todas"}
            </Link>
          );
        })}
      </div>

      {forecasts.length === 0 ? (
        <p className="glass rounded-lg p-8 text-center text-muted">
          No hay partidos en las próximas tres semanas.
        </p>
      ) : (
        [...byDay.entries()].map(([day, list]) => (
          <section key={day} className="flex flex-col gap-4">
            <h2 className="font-display text-xl font-bold capitalize">{dayLabel(list[0].kickoff)}</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {list.map((forecast) => (
                <ForecastCard key={forecast.match_id} forecast={forecast} />
              ))}
            </div>
          </section>
        ))
      )}

      <p className="text-center text-xs text-muted">
        Orientativo: no incluye lesiones, sanciones ni rotaciones.
      </p>
    </div>
  );
}
