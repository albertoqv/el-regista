"use client";

import Link from "next/link";
import { useState } from "react";
import { LeagueIngestionPanel } from "@/app/components/LeagueIngestionPanel";
import {
  ApiError,
  ingestApiFootballPlayer,
  ingestCompetition,
  ingestTransfermarktPlayer,
  type IngestionResult,
} from "@/lib/api";

function errorMessage(thrown: unknown): string {
  return thrown instanceof ApiError
    ? `La API respondió con un error (${thrown.status}).`
    : "No se ha podido conectar con la API.";
}

function IngestionResultCard({ result }: { result: IngestionResult }) {
  return (
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
            {result.skipped.length} omitido{result.skipped.length === 1 ? "" : "s"}:
          </p>
          <ul className="list-inside list-disc text-sm text-zinc-600 dark:text-zinc-400">
            {result.skipped.map((skipped) => (
              <li key={`${skipped.player_id}-${skipped.name}`}>
                {skipped.name} — {skipped.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function StatsBombIngestForm() {
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
      setResult(await ingestCompetition(Number(competitionId), Number(seasonId)));
    } catch (thrown) {
      setError(errorMessage(thrown));
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold tracking-tight">
        StatsBomb Open Data (competición histórica)
      </h2>
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
        tardar varios minutos: hay una petición HTTP por partido a StatsBomb y
        1-2 a Wikidata por cada jugador de cada alineación.
      </p>
      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}
      {result && <IngestionResultCard result={result} />}
    </section>
  );
}

function ApiFootballIngestForm() {
  const [name, setName] = useState("Bellingham");
  const [league, setLeague] = useState("140");
  const [season, setSeason] = useState("2023");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<IngestionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setResult(null);
    try {
      setResult(
        await ingestApiFootballPlayer(name, Number(league), Number(season)),
      );
    } catch (thrown) {
      setError(errorMessage(thrown));
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold tracking-tight">
        API-Football (jugador actual)
      </h2>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Trae un jugador actual por nombre, de la liga y temporada que elijas.
        Necesitas el id de liga de{" "}
        <a
          href="https://dashboard.api-football.com/"
          className="underline"
          target="_blank"
          rel="noreferrer"
        >
          API-Football
        </a>{" "}
        (La Liga = 140, verificado) y la temporada como año de inicio (p. ej.
        2023 para 2023/2024).
      </p>
      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
        <label className="flex flex-col gap-1 text-sm">
          Nombre del jugador
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Liga (ID)
          <input
            type="number"
            inputMode="numeric"
            value={league}
            onChange={(event) => setLeague(event.target.value)}
            className="w-24 rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Temporada
          <input
            type="number"
            inputMode="numeric"
            value={season}
            onChange={(event) => setSeason(event.target.value)}
            className="w-28 rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
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
        El plan gratuito de API-Football tiene un límite de 100 peticiones al
        día, así que esta ingesta trae un jugador cada vez, no una liga
        entera.
      </p>
      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}
      {result && <IngestionResultCard result={result} />}
    </section>
  );
}

function TransfermarktIngestForm() {
  const [playerId, setPlayerId] = useState("");
  const [name, setName] = useState("Jude Bellingham");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<IngestionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setResult(null);
    try {
      setResult(await ingestTransfermarktPlayer(Number(playerId), name));
    } catch (thrown) {
      setError(errorMessage(thrown));
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold tracking-tight">
        Transfermarkt (pie preferido y valor de mercado)
      </h2>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Enriquece un jugador que ya exista en la base de datos con su pie
        preferido y el histórico completo de valor de mercado de
        Transfermarkt. Usa el id del jugador (visible en su ficha) y el
        nombre por el que buscarlo.
      </p>
      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
        <label className="flex flex-col gap-1 text-sm">
          Player ID
          <input
            type="number"
            inputMode="numeric"
            value={playerId}
            onChange={(event) => setPlayerId(event.target.value)}
            className="w-32 rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Nombre en Transfermarkt
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          {pending ? "Enriqueciendo…" : "Enriquecer"}
        </button>
      </form>
      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}
      {result && <IngestionResultCard result={result} />}
    </section>
  );
}

export default function IngestPage() {
  return (
    <div className="flex flex-col gap-10">
      <h1 className="text-2xl font-semibold tracking-tight">Ingesta de datos</h1>
      <LeagueIngestionPanel />
      <hr className="border-zinc-200 dark:border-zinc-800" />
      <StatsBombIngestForm />
      <hr className="border-zinc-200 dark:border-zinc-800" />
      <ApiFootballIngestForm />
      <hr className="border-zinc-200 dark:border-zinc-800" />
      <TransfermarktIngestForm />
    </div>
  );
}
