"use client";

import Link from "next/link";
import { useState } from "react";
import { ApiError, ingestCompetition, type IngestionResult } from "@/lib/api";

export default function IngestPage() {
  const [competitionId, setCompetitionId] = useState("87");
  const [seasonId, setSeasonId] = useState("84");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<IngestionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setResult(null);
    try {
      const ingestionResult = await ingestCompetition(
        Number(competitionId),
        Number(seasonId),
      );
      setResult(ingestionResult);
    } catch (thrown) {
      setError(
        thrown instanceof ApiError
          ? `La API respondió con un error (${thrown.status}).`
          : "No se ha podido conectar con la API.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">
          Ingesta de StatsBomb Open Data
        </h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Introduce un `competition_id` y `season_id` reales de{" "}
          <a
            href="https://github.com/statsbomb/open-data"
            className="underline"
            target="_blank"
            rel="noreferrer"
          >
            StatsBomb Open Data
          </a>
          . Por defecto se rellena una final histórica de Copa del Rey (1 solo
          partido, rápida de probar).
        </p>
        <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-sm">
            Competition ID
            <input
              type="number"
              inputMode="numeric"
              value={competitionId}
              onChange={(event) => setCompetitionId(event.target.value)}
              className="rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Season ID
            <input
              type="number"
              inputMode="numeric"
              value={seasonId}
              onChange={(event) => setSeasonId(event.target.value)}
              className="rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <button
            type="submit"
            disabled={pending}
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            {pending ? "Ingiriendo…" : "Ingerir"}
          </button>
        </form>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          Para competiciones grandes (p. ej. un Mundial completo) esto puede
          tardar varios minutos: hay una petición HTTP por partido a StatsBomb
          y 1-2 a Wikidata por cada jugador que anotó.
        </p>
      </section>

      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}

      {result && (
        <section className="flex flex-col gap-3 rounded-md border border-zinc-200 p-6 dark:border-zinc-800">
          <p className="text-lg font-medium">
            {result.ingested} jugador{result.ingested === 1 ? "" : "es"} ingerido
            {result.ingested === 1 ? "" : "s"}.{" "}
            <Link href="/" className="underline">
              Ver jugadores
            </Link>
          </p>
          {result.skipped.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                {result.skipped.length} omitido
                {result.skipped.length === 1 ? "" : "s"} (sin fecha de
                nacimiento fiable):
              </p>
              <ul className="list-inside list-disc text-sm text-zinc-600 dark:text-zinc-400">
                {result.skipped.map((skipped) => (
                  <li key={skipped.player_id}>{skipped.name}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
