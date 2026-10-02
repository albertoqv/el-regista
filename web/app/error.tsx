"use client"; // Error boundaries must be Client Components

import Link from "next/link";
import { ScoutNote } from "@/app/components/ScoutNote";

export default function Error({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center gap-4 py-20 text-center">
      <ScoutNote rotate={-3}>el VAR está revisando…</ScoutNote>
      <h1 className="font-display text-4xl font-bold tracking-tight">Algo se ha torcido</h1>
      <p className="text-sm text-muted">
        No hemos podido cargar los datos. Suele ser un momento puntual del servidor: vuelve a
        intentarlo en unos segundos.
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => retry()}
          className="rounded-full bg-[#c93c17] px-5 py-2.5 text-sm font-bold text-bg transition hover:brightness-105"
        >
          Reintentar
        </button>
        <Link href="/" className="rounded-full border border-line px-5 py-2.5 text-sm text-muted hover:text-ink">
          Ir a la portada
        </Link>
      </div>
      {error.digest ? <p className="text-xs text-muted/60">Código: {error.digest}</p> : null}
    </div>
  );
}
