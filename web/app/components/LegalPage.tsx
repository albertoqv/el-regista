import type { ReactNode } from "react";

export const CONTACT_URL = "https://github.com/albertoqv/el-regista/issues";

/** Plain reading page for the legal texts: one column, short sections. */
export function LegalPage({ title, updated, children }: { title: string; updated: string; children: ReactNode }) {
  return (
    <article className="mx-auto flex max-w-2xl flex-col gap-8 py-6">
      <header className="flex flex-col gap-2">
        <h1 className="font-display text-5xl leading-[0.92] sm:text-6xl">{title}</h1>
        <p className="text-sm text-muted">Actualizado el {updated}</p>
      </header>
      {children}
    </article>
  );
}

export function LegalSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-3 text-base leading-relaxed">
      <h2 className="font-heading text-xl tracking-tight">{title}</h2>
      {children}
    </section>
  );
}

export function External({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="font-semibold underline decoration-line underline-offset-4 hover:text-brand">
      {children}
    </a>
  );
}
