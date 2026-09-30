import Link from "next/link";
import { Logo } from "@/app/components/Logo";

const LINKS = [
  { href: "/explorar", label: "Explorar" },
  { href: "/equipos", label: "Equipos" },
  { href: "/predicciones", label: "Predicciones" },
];

export function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-[#04060c]/70 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 sm:px-6">
        <Link href="/" aria-label="TalentScope, inicio" className="shrink-0">
          <Logo size={22} />
        </Link>
        <div className="no-scrollbar -mr-4 ml-auto flex items-center gap-0.5 overflow-x-auto pr-4 text-xs font-medium sm:mr-0 sm:gap-1 sm:pr-0 sm:text-sm">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="shrink-0 rounded-full px-3 py-1.5 text-muted transition hover:bg-white/5 hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="/gemelos"
            className="relative shrink-0 rounded-full px-3 py-1.5 font-semibold text-[#ffd76a] transition hover:bg-[#ffd76a]/10"
          >
            Gemelos
          </Link>
          <Link
            href="/compare"
            className="shrink-0 rounded-full bg-gradient-to-r from-brand to-brand-2 px-4 py-1.5 font-semibold text-white shadow-[0_0_20px_rgba(61,139,255,0.45)] transition hover:brightness-110"
          >
            Comparar
          </Link>
        </div>
      </nav>
    </header>
  );
}
