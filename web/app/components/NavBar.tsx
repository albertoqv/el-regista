import Link from "next/link";
import { Logo } from "@/app/components/Logo";

export function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-[#04060c]/70 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link href="/" aria-label="TalentScope, inicio">
          <Logo size={22} />
        </Link>
        <div className="flex items-center gap-1 text-sm font-medium">
          <Link
            href="/"
            className="rounded-full px-3 py-1.5 text-muted transition hover:bg-white/5 hover:text-ink"
          >
            Explorar
          </Link>
          <Link
            href="/compare"
            className="rounded-full bg-gradient-to-r from-brand to-brand-2 px-4 py-1.5 font-semibold text-white shadow-[0_0_20px_rgba(61,139,255,0.45)] transition hover:brightness-110"
          >
            Comparar
          </Link>
        </div>
      </nav>
    </header>
  );
}
