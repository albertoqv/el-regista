import Link from "next/link";
import type { ReactNode } from "react";
import { ProductIcon } from "@/app/components/ProductIcon";
import { PHOTOS } from "@/lib/photos";
import { PRODUCTS, type Product } from "@/lib/products";

const PRODUCT_PHOTOS = { scout: PHOTOS.scout.src, pronosticos: PHOTOS.pronosticos.src };

/** The two products side by side, each with its tools. */
export function ProductsGrid() {
  return (
    <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {PRODUCTS.map((product) => (
        <div
          key={product.key}
          className="glass relative overflow-hidden rounded-xl p-5 sm:p-7"
          style={{ borderTop: `4px solid ${product.color}` }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={PRODUCT_PHOTOS[product.key]} alt="" className="-mx-5 -mt-5 mb-5 h-36 w-[calc(100%+2.5rem)] max-w-none object-cover sm:-mx-7 sm:-mt-7 sm:w-[calc(100%+3.5rem)]" />
          <p className="text-xs font-semibold uppercase tracking-[0.2em]" style={{ color: product.color }}>
            {product.subject}
          </p>
          <h2 className="font-display text-4xl">{product.name}</h2>
          <div className="mt-4 grid grid-cols-2 gap-2 sm:mt-5">
            {product.tools.map((tool) => (
              <Link
                key={tool.href}
                href={tool.href}
                className="flex items-center gap-2.5 rounded-lg border border-line bg-white/[0.02] p-2.5 transition hover:border-line-strong hover:bg-white/[0.05] sm:items-start sm:gap-3 sm:p-3"
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/5 sm:h-9 sm:w-9">
                  <ProductIcon name={tool.icon} color={product.color} />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold leading-tight">{tool.label}</span>
                  <span className="hidden text-xs text-muted sm:block">{tool.description}</span>
                </span>
              </Link>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}

/** Heading that opens each product's block on the home page. */
export function ProductBand({
  product,
  title,
  children,
}: {
  product: Product["key"];
  title: string;
  children: ReactNode;
}) {
  const info = PRODUCTS.find((entry) => entry.key === product) as Product;
  return (
    <section className="flex flex-col gap-10">
      <div className="flex items-end justify-between gap-4 border-b border-line pb-4">
        <div>
          <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.25em]" style={{ color: info.color }}>
            <span className="h-2 w-2 rounded-full" style={{ background: info.color }} />
            {info.subject}
          </p>
          <h2 className="font-display text-4xl sm:text-5xl">{title}</h2>
        </div>
        <Link href={info.tools[0].href} className="hidden shrink-0 text-sm font-semibold hover:underline sm:block" style={{ color: info.color }}>
          Abrir {info.name} →
        </Link>
      </div>
      {children}
    </section>
  );
}
