import Link from "next/link";

export function NavBar() {
  return (
    <header className="border-b border-black/10 dark:border-white/10">
      <nav className="mx-auto flex max-w-4xl flex-wrap items-center gap-4 px-4 py-4 sm:gap-6 sm:px-6">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          ⚽ Player Scouting
        </Link>
        <div className="flex gap-4 text-sm font-medium text-zinc-600 dark:text-zinc-400">
          <Link href="/" className="hover:text-zinc-950 dark:hover:text-zinc-50">
            Jugadores
          </Link>
          <Link
            href="/compare"
            className="hover:text-zinc-950 dark:hover:text-zinc-50"
          >
            Comparar
          </Link>
          <Link href="/ingest" className="hover:text-zinc-950 dark:hover:text-zinc-50">
            Ingesta
          </Link>
        </div>
      </nav>
    </header>
  );
}
