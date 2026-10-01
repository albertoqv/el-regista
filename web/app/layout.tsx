import { Analytics } from "@vercel/analytics/next";
import type { Metadata } from "next";
import { Chivo } from "next/font/google";
import localFont from "next/font/local";
import Link from "next/link";
import { NavBar } from "@/app/components/NavBar";
import { VisitTracker } from "@/app/components/VisitTracker";
import { PHOTOS } from "@/lib/photos";
import { PRODUCTS } from "@/lib/products";
import { SITE_URL } from "@/lib/site";
import "./globals.css";

const chivo = Chivo({
  variable: "--font-chivo",
  subsets: ["latin"],
});

// Our own typeface, drawn for El Regista (scripts/brand/regista_font.py).
const regista = localFont({
  src: "./fonts/RegistaDisplay.woff2",
  variable: "--font-regista",
  display: "swap",
  fallback: ["Arial Narrow", "sans-serif"],
});

export const metadata: Metadata = {
  // Absolute URLs for social previews (Open Graph cards).
  metadataBase: new URL(SITE_URL),
  title: "El Regista",
  description: "Scout y pronósticos de fútbol con datos reales.",
  openGraph: {
    siteName: "El Regista",
    locale: "es_ES",
    type: "website",
  },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${chivo.variable} ${regista.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <NavBar />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-24 pt-6 sm:px-6">{children}</main>
        <footer className="border-t border-line bg-bg-deep py-10 text-xs text-muted">
          <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 sm:px-6">
            <nav className="flex flex-wrap gap-x-5 gap-y-2 text-sm">
              {PRODUCTS.flatMap((product) =>
                product.tools.map((tool) => (
                  <Link key={tool.href} href={tool.href} className="hover:text-ink">
                    {tool.label}
                  </Link>
                )),
              )}
              <Link href="/como-funciona" className="hover:text-ink">
                Cómo funciona
              </Link>
            </nav>
            <p>Datos: FBref, Understat, Transfermarkt y football-data. Se actualiza martes y viernes.</p>
            <p>
              Fotos:{" "}
              {Object.values(PHOTOS).map((photo, index) => (
                <span key={photo.src}>
                  {index > 0 ? " · " : ""}
                  <a href={photo.source} target="_blank" rel="noreferrer" className="hover:text-ink">
                    {photo.author}
                  </a>{" "}
                  (
                  <a href={photo.licenseUrl} target="_blank" rel="noreferrer" className="hover:text-ink">
                    {photo.license}
                  </a>
                  )
                </span>
              ))}
            </p>
          </div>
        </footer>
        <VisitTracker />
        <Analytics />
      </body>
    </html>
  );
}
