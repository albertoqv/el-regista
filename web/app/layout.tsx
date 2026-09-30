import type { Metadata } from "next";
import { Caveat, Inter, Space_Grotesk } from "next/font/google";
import { NavBar } from "@/app/components/NavBar";
import { TacticsBackground } from "@/app/components/TacticsBackground";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const caveat = Caveat({
  variable: "--font-caveat",
  subsets: ["latin"],
});

const grotesk = Space_Grotesk({
  variable: "--font-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  // Absolute URLs for social previews (Open Graph cards).
  metadataBase: new URL(
    process.env.VERCEL_PROJECT_PRODUCTION_URL
      ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
      : "http://localhost:3000",
  ),
  title: "TalentScope",
  description:
    "Compara futbolistas, descubre talento parecido y analiza su rendimiento con datos reales de las 5 grandes ligas",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${inter.variable} ${grotesk.variable} ${caveat.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        <TacticsBackground />
        <NavBar />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-24 pt-6 sm:px-6">
          {children}
        </main>
        <footer className="border-t border-line py-10 text-center text-xs text-muted">
          <p className="font-hand text-lg text-ink/70">
            Hecho por gente que ve demasiado fútbol.
          </p>
          <p className="mt-1">Datos: FBref, Understat y Transfermarkt · Actualizado cada semana</p>
        </footer>
      </body>
    </html>
  );
}
