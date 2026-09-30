import Link from "next/link";
import { ScoutNote } from "@/app/components/ScoutNote";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center gap-4 py-20 text-center">
      <ScoutNote rotate={2}>fuera de juego</ScoutNote>
      <h1 className="font-display text-4xl font-bold tracking-tight">Aquí no hay nadie</h1>
      <p className="text-sm text-muted">
        Esta página no existe o el jugador ya no está en nuestra base de datos. Búscalo de nuevo o
        explora por filtros.
      </p>
      <div className="flex gap-2">
        <Link
          href="/"
          className="rounded-full bg-[#ffd76a] px-5 py-2.5 text-sm font-bold text-black transition hover:brightness-105"
        >
          Buscar jugador
        </Link>
        <Link href="/explorar" className="rounded-full border border-line px-5 py-2.5 text-sm text-muted hover:text-ink">
          Explorador
        </Link>
      </div>
    </div>
  );
}
