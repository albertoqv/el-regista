import Image from "next/image";
import Link from "next/link";
import { PHOTOS } from "@/lib/photos";

export default function NotFound() {
  return (
    <section className="photo-header -mx-4 -mt-6 flex min-h-[70vh] flex-col items-start justify-end gap-4 px-4 pb-12 sm:mx-0 sm:mt-0 sm:rounded-xl sm:px-10">
      <Image src={PHOTOS.no_encontrado.src} alt="" fill sizes="100vw" className="object-cover" />
      <h1 className="font-display text-6xl leading-[0.92] sm:text-7xl">Aquí no hay nadie</h1>
      <p className="text-ink/85">Esta página no existe.</p>
      <div className="flex gap-2">
        <Link href="/buscar" className="rounded-md bg-brand px-5 py-2.5 text-sm font-semibold text-bg">
          Buscar jugador
        </Link>
        <Link href="/" className="rounded-md border border-line-strong px-5 py-2.5 text-sm text-ink">
          Portada
        </Link>
      </div>
    </section>
  );
}
