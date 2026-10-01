"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { IconChevron, IconClose, IconMenu } from "@/app/components/icons";
import { Logo } from "@/app/components/Logo";
import { ProductIcon } from "@/app/components/ProductIcon";
import { locate, PRODUCTS, type Product } from "@/lib/products";

function ProductMenu({ product, active }: { product: Product; active: boolean }) {
  return (
    <div className="group relative">
      <button
        type="button"
        className={`flex items-center gap-1 rounded-full px-3 py-1.5 text-sm font-medium transition hover:bg-white/5 ${active ? "text-ink" : "text-muted hover:text-ink"}`}
        aria-haspopup="true"
      >
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: product.color }} />
        {product.name}
        <IconChevron size={14} color="currentColor" />
      </button>
      {/* Opens on hover and on keyboard focus; the padding bridges the gap. */}
      <div className="invisible absolute left-0 top-full z-50 pt-2 opacity-0 transition group-focus-within:visible group-focus-within:opacity-100 group-hover:visible group-hover:opacity-100">
        <div className="w-80 rounded-lg border border-line bg-bg-deep p-2">
          <p className="px-3 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: product.color }}>
            {product.subject}
          </p>
          {product.tools.map((tool) => (
            <Link
              key={tool.href}
              href={tool.href}
              className="flex items-start gap-3 rounded-lg px-3 py-2.5 transition hover:bg-white/5"
            >
              <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/5">
                <ProductIcon name={tool.icon} color={product.color} />
              </span>
              <span>
                <span className="block text-sm font-semibold text-ink">{tool.label}</span>
                <span className="block text-xs text-muted">{tool.description}</span>
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

function MobileMenu({ onClose }: { onClose: () => void }) {
  // Outside the header on purpose: its backdrop blur would clip a fixed child.
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-[#1f3b2d] px-4 pb-10 md:hidden" role="dialog" aria-modal="true" aria-label="Menú">
      <div className="sticky top-0 -mx-4 mb-4 flex items-center justify-between border-b border-line bg-[#1f3b2d] px-4 py-3">
        <Link href="/" onClick={onClose} aria-label="El Regista, inicio">
          <Logo size={22} />
        </Link>
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar menú"
          className="flex h-9 w-9 items-center justify-center rounded-full border border-line"
        >
          <IconClose size={18} color="currentColor" />
        </button>
      </div>
      {PRODUCTS.map((product) => (
        <section key={product.key} className="mb-6">
          <p className="mb-1 flex items-center gap-2 px-1 text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: product.color }}>
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: product.color }} />
            {product.name} · {product.subject}
          </p>
          <div className="flex flex-col">
            {product.tools.map((tool) => (
              <Link
                key={tool.href}
                href={tool.href}
                onClick={onClose}
                className="flex items-center gap-3 rounded-lg px-2 py-3 active:bg-white/5"
              >
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/5">
                  <ProductIcon name={tool.icon} color={product.color} />
                </span>
                <span className="min-w-0">
                  <span className="block font-semibold">{tool.label}</span>
                  <span className="block truncate text-xs text-muted">{tool.description}</span>
                </span>
              </Link>
            ))}
          </div>
        </section>
      ))}
      <Link href="/como-funciona" onClick={onClose} className="block px-2 py-3 text-sm text-muted">
        Cómo funciona →
      </Link>
    </div>
  );
}

function ProductTabs({ product, activeHref }: { product: Product; activeHref: string }) {
  return (
    <div className="border-t border-line/60">
      <div className="no-scrollbar mx-auto flex max-w-6xl items-center gap-1 overflow-x-auto px-4 py-1.5 sm:px-6">
        <span className="mr-2 shrink-0 text-[11px] font-semibold uppercase tracking-[0.18em]" style={{ color: product.color }}>
          {product.name}
        </span>
        {product.tools.map((tool) => {
          const active = tool.href === activeHref;
          return (
            <Link
              key={tool.href}
              href={tool.href}
              aria-current={active ? "page" : undefined}
              // On phones the tab row scrolls: bring the current tool into view.
              ref={active ? (element) => element?.scrollIntoView({ block: "nearest", inline: "center" }) : undefined}
              className={`flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition ${active ? "bg-white/10 text-ink" : "text-muted hover:text-ink"}`}
            >
              <ProductIcon name={tool.icon} size={14} color={active ? product.color : "currentColor"} />
              {tool.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export function NavBar() {
  const pathname = usePathname() ?? "/";
  const [open, setOpen] = useState(false);
  const here = locate(pathname);

  // Menu links close it themselves; while open, the page behind does not scroll.
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <header className="sticky top-0 z-40 border-b border-line bg-bg/95">
        <nav className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-3 sm:px-6">
          <Link href="/" aria-label="El Regista, inicio" className="shrink-0">
            <Logo size={22} />
          </Link>
          <div className="ml-4 hidden items-center gap-1 md:flex">
            {PRODUCTS.map((product) => (
              <ProductMenu key={product.key} product={product} active={here?.product.key === product.key} />
            ))}
            <Link href="/como-funciona" className="rounded-full px-3 py-1.5 text-sm text-muted transition hover:bg-white/5 hover:text-ink">
              Cómo funciona
            </Link>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Link
              href="/gemelos"
              className="hidden shrink-0 rounded-full px-3 py-1.5 text-sm font-semibold text-[#f2c230] transition hover:bg-[#f2c230]/10 sm:block"
            >
              Gemelos
            </Link>
            <Link
              href="/predicciones"
              className="shrink-0 rounded-full bg-brand px-4 py-1.5 text-sm font-semibold text-bg transition hover:brightness-110"
            >
              Pronósticos
            </Link>
            <button
              type="button"
              onClick={() => setOpen((value) => !value)}
              aria-label={open ? "Cerrar menú" : "Abrir menú"}
              aria-expanded={open}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-line md:hidden"
            >
              {open ? <IconClose size={18} color="currentColor" /> : <IconMenu size={18} color="currentColor" />}
            </button>
          </div>
        </nav>
        {here ? <ProductTabs product={here.product} activeHref={here.tool.href} /> : null}
      </header>
      {open ? <MobileMenu onClose={() => setOpen(false)} /> : null}
    </>
  );
}
