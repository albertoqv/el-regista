import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";
import { PHOTOS } from "@/lib/photos";
import { PRODUCTS, type Product } from "@/lib/products";

const PRODUCT_PHOTOS = { scout: PHOTOS.scout.src, pronosticos: PHOTOS.pronosticos.src };

/** The two products side by side: a photo, the name and its tools as a plain list. */
export function ProductsGrid() {
  return (
    <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {PRODUCTS.map((product) => (
        <div key={product.key} className="glass overflow-hidden" style={{ borderTop: `4px solid ${product.color}` }}>
          <Image
            src={PRODUCT_PHOTOS[product.key]}
            alt=""
            width={1024}
            height={683}
            sizes="(min-width: 768px) 552px, 100vw"
            className="h-40 w-full object-cover"
          />
          <div className="p-5 sm:p-7">
            <h2 className="font-display text-5xl" style={{ color: product.color }}>
              {product.name}
            </h2>
            <ul className="mt-3 divide-y divide-line">
              {product.tools.map((tool) => (
                <li key={tool.href}>
                  <Link href={tool.href} className="group/tool flex items-baseline justify-between gap-4 py-3">
                    <span className="font-heading text-2xl leading-none transition group-hover/tool:text-brand">{tool.label}</span>
                    <span className="hidden text-right text-sm text-muted sm:block">{tool.description}</span>
                  </Link>
                </li>
              ))}
            </ul>
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
      <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-1 border-b border-line pb-4">
        <h2 className="font-display text-4xl sm:text-6xl" style={{ color: info.color }}>
          {title}
        </h2>
        <Link href={info.tools[0].href} className="font-heading text-lg hover:underline sm:text-xl">
          Abrir {info.name} →
        </Link>
      </div>
      {children}
    </section>
  );
}
