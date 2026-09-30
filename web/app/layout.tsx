import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import { NavBar } from "@/app/components/NavBar";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const grotesk = Space_Grotesk({
  variable: "--font-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TalentScope",
  description:
    "Compara futbolistas, descubre talento parecido y analiza su rendimiento con datos reales de las 5 grandes ligas",
};

function Aurora() {
  return (
    <div className="aurora" aria-hidden="true">
      <div
        className="aurora-blob"
        style={{
          width: "46vw",
          height: "46vw",
          left: "-12vw",
          top: "-18vw",
          background: "radial-gradient(circle, #1d4ed8, transparent 65%)",
        }}
      />
      <div
        className="aurora-blob"
        style={{
          width: "38vw",
          height: "38vw",
          right: "-10vw",
          top: "-8vw",
          background: "radial-gradient(circle, #0891b2, transparent 65%)",
          animationDelay: "-7s",
        }}
      />
      <div
        className="aurora-blob"
        style={{
          width: "34vw",
          height: "34vw",
          left: "30vw",
          top: "55vh",
          background: "radial-gradient(circle, #6d28d9, transparent 65%)",
          opacity: 0.25,
          animationDelay: "-13s",
        }}
      />
    </div>
  );
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${inter.variable} ${grotesk.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        <Aurora />
        <NavBar />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-24 pt-6 sm:px-6">
          {children}
        </main>
        <footer className="border-t border-line py-8 text-center text-xs text-muted">
          Datos: FBref, Understat y Transfermarkt · Actualizado cada semana
        </footer>
      </body>
    </html>
  );
}
