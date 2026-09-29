"use client";

import { useEffect, useState } from "react";
import { LeagueAutocomplete } from "@/app/components/LeagueAutocomplete";
import {
  ApiError,
  enqueueLeagueIngestion,
  listLeagueIngestionJobs,
  processLeagueIngestionBatch,
  type LeagueIngestionJob,
  type LeagueSummary,
} from "@/lib/api";

const AVAILABLE_SEASONS = [
  { year: 2022, label: "2022/23" },
  { year: 2023, label: "2023/24" },
  { year: 2024, label: "2024/25" },
];

function errorMessage(thrown: unknown): string {
  return thrown instanceof ApiError
    ? `La API respondió con un error (${thrown.status}).`
    : "No se ha podido conectar con la API.";
}

function jobProgressLabel(job: LeagueIngestionJob): string {
  if (job.is_completed) {
    return `Completo (${job.total_pages} páginas)`;
  }
  if (job.total_pages === null) {
    return "Esperando primera página…";
  }
  return `Página ${job.next_page - 1}/${job.total_pages}`;
}

export function LeagueIngestionPanel() {
  const [league, setLeague] = useState<LeagueSummary | null>(null);
  const [seasonYear, setSeasonYear] = useState(AVAILABLE_SEASONS[1].year);
  const [jobs, setJobs] = useState<LeagueIngestionJob[]>([]);
  const [enqueuing, setEnqueuing] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastBatchMessage, setLastBatchMessage] = useState<string | null>(null);

  function refreshJobs() {
    listLeagueIngestionJobs()
      .then(setJobs)
      .catch(() => setJobs([]));
  }

  useEffect(() => {
    refreshJobs();
  }, []);

  async function handleEnqueue() {
    if (!league) return;
    setEnqueuing(true);
    setError(null);
    try {
      await enqueueLeagueIngestion(league.id, league.name, seasonYear);
      refreshJobs();
    } catch (thrown) {
      setError(errorMessage(thrown));
    } finally {
      setEnqueuing(false);
    }
  }

  async function handleProcessNow() {
    setProcessing(true);
    setError(null);
    setLastBatchMessage(null);
    try {
      const summary = await processLeagueIngestionBatch();
      setLastBatchMessage(
        `${summary.pages_processed} página${summary.pages_processed === 1 ? "" : "s"} procesada${summary.pages_processed === 1 ? "" : "s"}, ${summary.players_ingested} jugador${summary.players_ingested === 1 ? "" : "es"} ingerido${summary.players_ingested === 1 ? "" : "s"}.`,
      );
      refreshJobs();
    } catch (thrown) {
      setError(errorMessage(thrown));
    } finally {
      setProcessing(false);
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold tracking-tight">
        Ingesta masiva por liga y temporada
      </h2>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        Busca una liga por nombre, elige la temporada y encólala: se ingiere en
        páginas de 20 jugadores. El plan gratuito de API-Football limita a 100
        peticiones al día, así que una liga completa (varias decenas de
        páginas) se reparte en varios días automáticamente — el botón
        &quot;Procesar ahora&quot; adelanta un lote manualmente.
      </p>
      <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
        El plan gratuito solo da acceso a las temporadas 2022/23, 2023/24 y
        2024/25 — ninguna de ellas es la temporada real en curso, y no hay más
        rango disponible sin pasar a un plan de pago.
      </p>
      <div className="flex flex-wrap items-end gap-2">
        <LeagueAutocomplete
          selected={league}
          onSelect={setLeague}
          placeholder="Buscar liga (ej. La Liga, Serie A)…"
        />
        <label className="flex flex-col gap-1 text-sm">
          Temporada
          <select
            value={seasonYear}
            onChange={(event) => setSeasonYear(Number(event.target.value))}
            className="rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
          >
            {AVAILABLE_SEASONS.map((season) => (
              <option key={season.year} value={season.year}>
                {season.label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={handleEnqueue}
          disabled={!league || enqueuing}
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          {enqueuing ? "Encolando…" : "Encolar ingesta masiva"}
        </button>
        <button
          type="button"
          onClick={handleProcessNow}
          disabled={processing}
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium hover:border-zinc-500 disabled:opacity-50 dark:border-zinc-700"
        >
          {processing ? "Procesando…" : "Procesar ahora"}
        </button>
      </div>

      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}
      {lastBatchMessage && (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          {lastBatchMessage}
        </p>
      )}

      {jobs.length > 0 && (
        <div className="overflow-x-auto rounded-md border border-zinc-200 dark:border-zinc-800">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-zinc-200 text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
              <tr>
                <th className="px-3 py-2 font-medium">Liga</th>
                <th className="px-3 py-2 font-medium">Temporada</th>
                <th className="px-3 py-2 font-medium">Progreso</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td className="px-3 py-2">{job.league_name}</td>
                  <td className="px-3 py-2">{job.season_year}</td>
                  <td className="px-3 py-2">{jobProgressLabel(job)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
