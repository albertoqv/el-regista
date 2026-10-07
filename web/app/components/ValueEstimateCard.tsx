import Link from "next/link";
import type { ValueEstimate } from "@/lib/api";
import { formatMarketValue } from "@/lib/format";

// Factors closer to 1 than this say nothing worth a line.
const QUIET = 0.08;

function verdict(ratio: number): string {
  if (ratio >= 1.3) return "Rinde por encima de su precio";
  if (ratio <= 0.77) return "Su precio va por delante de su rendimiento";
  return "Su precio cuadra con lo que rinde";
}

function factor(value: number): string {
  return `×${value.toFixed(2).replace(".", ",")}`;
}

/** What the model says he is worth from his last season, and why. */
export function ValueEstimateCard({ estimate }: { estimate: ValueEstimate }) {
  const factors = estimate.factors.filter((f) => Math.abs(f.factor - 1) >= QUIET).slice(0, 4);
  const ratio = estimate.market_eur ? estimate.estimate_eur / estimate.market_eur : null;
  const error = Math.round(estimate.model.median_error * 100);

  return (
    <section className="flex flex-col gap-4">
      <div>
        <h2 className="font-heading text-2xl tracking-tight">Lo que vale por lo que rinde</h2>
        <p className="text-sm text-muted">
          Valor estimado por un modelo con su última temporada (liga, edad, posición, goles,
          asistencias, minutos, Europa y selección).{" "}
          <Link href="/infravalorados" className="underline hover:text-ink">
            Ver los más infravalorados
          </Link>
          .
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="glass rounded-lg p-4">
          <span className="block font-display text-4xl tabular-nums">{formatMarketValue(estimate.estimate_eur)}</span>
          <span className="text-sm text-muted">Estimado por su rendimiento</span>
        </div>
        <div className="glass rounded-lg p-4">
          <span className="block font-display text-4xl tabular-nums">
            {estimate.market_eur ? formatMarketValue(estimate.market_eur) : "—"}
          </span>
          <span className="text-sm text-muted">Valor de mercado (Transfermarkt)</span>
        </div>
      </div>
      {ratio && <p className="font-semibold">{verdict(ratio)}.</p>}
      {factors.length > 0 && (
        <ul className="flex flex-col gap-1 text-sm">
          {factors.map((f) => (
            <li key={f.label} className="flex justify-between border-b border-line/60 py-1">
              <span>{f.label}</span>
              <span className={`tabular-nums ${f.factor > 1 ? "text-ink" : "text-muted"}`}>{factor(f.factor)}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="text-sm text-muted">
        Cada factor multiplica el valor de un jugador medio. El modelo se equivoca en un {error}% de mediana con
        jugadores que no vio al aprender: es una referencia, no un precio.
      </p>
    </section>
  );
}
