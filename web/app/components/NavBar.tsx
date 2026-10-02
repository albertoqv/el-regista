"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { IconChevron, IconClose, IconMenu } from "@/app/components/icons";
import { Logo } from "@/app/components/Logo";
import { locate, PRODUCTS, type Product } from "@/lib/products";

/** One tool in a menu: its name in our own lettering and one plain line below. */
function ToolLink({
  href,
  label,
  description,
  onClick,
}: {
  href: string;
  label: string;
  description: string;
  onClick?: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className="group/tool block border-l-2 border-transparent px-4 py-2.5 transition hover:border-brand hover:bg-ink/[0.04]"
    >
      <span className="block font-heading text-2xl leading-none text-ink transition group-hover/tool:text-brand">{label}</span>
      <span className="mt-1 block text-sm text-muted">{description}</span>
    </Link>
  );
}

function ProductMenu({ product, active }: { product: Product; active: boolean }) {
  return (
    <div className="group relative">
      <button
        type="button"
        className={`flex items-center gap-1 px-3 py-1.5 font-heading text-xl transition ${active ? "text-brand" : "text-ink hover:text-brand"}`}
        aria-haspopup="true"
      >
        {product.name}
        <IconChevron size={14} color="currentColor" />
      </button>
      {/* Opens on hover and on keyboard focus; the padding bridges the gap. */}
      <div className="invisible absolute left-0 top-full z-50 pt-2 opacity-0 transition group-focus-within:visible group-focus-within:opacity-100 group-hover:visible group-hover:opacity-100">
        <div className="w-80 border border-line bg-bg-deep py-2">
          {product.tools.map((tool) => (
            <ToolLink key={tool.href} href={tool.href} label={tool.label} description={tool.description} />
          ))}
        </div>
      </div>
    </div>
  );
}

function MobileMenu({ onClose }: { onClose: () => void }) {
  // Outside the header on purpose: a fixed child of the sticky header gets clipped.
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-bg-deep pb-10 md:hidden" role="dialog" aria-modal="true" aria-label="Menú">
      <div className="sticky top-0 flex items-center justify-between border-b border-line bg-bg-deep px-4 py-3">
        <Link href="/" onClick={onClose} aria-label="El Regista, inicio">
          <Logo size={22} />
        </Link>
        <button type="button" onClick={onClose} aria-label="Cerrar menú" className="flex h-9 w-9 items-center justify-center border border-line">
          <IconClose size={18} color="currentColor" />
        </button>
      </div>
      {PRODUCTS.map((product) => (
        <section key={product.key} className="mt-6">
          <h2 className="px-4 pb-1 font-display text-4xl" style={{ color: product.color }}>
            {product.name}
          </h2>
          {product.tools.map((tool) => (
            <ToolLink key={tool.href} href={tool.href} label={tool.label} description={tool.description} onClick={onClose} />
          ))}
        </section>
      ))}
      <Link href="/como-funciona" onClick={onClose} className="mt-6 block px-4 py-3 font-heading text-2xl text-muted">
        Cómo funciona
      </Link>
    </div>
  );
}

function ProductTabs({ product, activeHref }: { product: Product; activeHref: string }) {
  return (
    <div className="border-t border-line">
      <div className="no-scrollbar mx-auto flex max-w-6xl items-end gap-5 overflow-x-auto px-4 sm:px-6">
        {product.tools.map((tool) => {
          const active = tool.href === activeHref;
          return (
            <Link
              key={tool.href}
              href={tool.href}
              aria-current={active ? "page" : undefined}
              // On phones the tab row scrolls: bring the current tool into view.
              ref={active ? (element) => element?.scrollIntoView({ block: "nearest", inline: "center" }) : undefined}
              className={`shrink-0 border-b-2 py-2 font-heading text-lg transition ${active ? "border-brand text-ink" : "border-transparent text-muted hover:text-ink"}`}
            >
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
      <header className="sticky top-0 z-40 border-b border-line bg-bg">
        <nav className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-3 sm:px-6">
          <Link href="/" aria-label="El Regista, inicio" className="shrink-0">
            <Logo size={22} />
          </Link>
          <div className="ml-4 hidden items-center gap-1 md:flex">
            {PRODUCTS.map((product) => (
              <ProductMenu key={product.key} product={product} active={here?.product.key === product.key} />
            ))}
            <Link href="/como-funciona" className="px-3 py-1.5 font-heading text-xl text-muted transition hover:text-ink">
              Cómo funciona
            </Link>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Link href="/predicciones" className="shrink-0 bg-brand px-4 py-1.5 font-heading text-lg text-bg transition hover:brightness-110">
              Pronósticos
            </Link>
            <button
              type="button"
              onClick={() => setOpen((value) => !value)}
              aria-label={open ? "Cerrar menú" : "Abrir menú"}
              aria-expanded={open}
              className="flex h-9 w-9 items-center justify-center border border-line md:hidden"
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
