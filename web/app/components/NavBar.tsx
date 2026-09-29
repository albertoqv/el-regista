import Link from "next/link";
import { Logo } from "@/app/components/Logo";

export function NavBar() {
  return (
    <header className="border-b border-black/10 dark:border-white/10">
      <nav className="mx-auto flex max-w-4xl flex-wrap items-center gap-4 px-4 py-4 sm:gap-6 sm:px-6">
        <Link href="/">
          <Logo size={30} />
        </Link>
        <div className="flex gap-4 text-sm font-medium text-zinc-600 dark:text-zinc-400">
          <Link href="/" className="hover:opacity-80">
            Jugadores
          </Link>
          <Link href="/compare" className="hover:opacity-80">
            Comparar
          </Link>
        </div>
      </nav>
    </header>
  );
}
