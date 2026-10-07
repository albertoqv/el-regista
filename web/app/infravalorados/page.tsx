import type { Metadata } from "next";
import Link from "next/link";
import { Avatar } from "@/app/components/Avatar";
import { PageHeader } from "@/app/components/PageHeader";
import { getValueGaps, type ValueGap } from "@/lib/api";
import { formatMarketValue, positionLabel } from "@/lib/format";
import { PHOTOS } from "@/lib/photos";

export const metadata: Metadata = {
  title: "Infravalorados · El Regista",
  description:
    "Jugadores que rinden como si valieran mucho más: valor estimado por un modelo frente al valor de mercado.",
  alternates: { canonical: "/infravalorados" },
};

const POSITIONS = ["", "Forward", "Midfielder", "Defender"];

function param(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value) ?? "";
}

function ratio(value: number): string {
  return `×${value.toFixed(1).replace(".", ",")}`;
}

function Row({ gap, rank }: { gap: ValueGap; rank: number }) {
  return (
    <li className="border-b border-line">
      <Link href={`/players/${gap.player_id}`} className="flex items-center gap-3 py-3 hover:text-brand">
        <span className="w-6 shrink-0 text-right text-sm tabular-nums text-muted">{rank}</span>
        <Avatar name={gap.name} photoUrl={gap.photo_url} size={44} />
        <span className="min-w-0 flex-1">
          <span className="block truncate font-semibold">{gap.name}</span>
          <span className="block truncate text-sm text-muted">
            {positionLabel(gap.position)}
            {gap.club ? ` · ${gap.club}` : ""}
          </span>
        </span>
        <span className="shrink-0 text-right">
          <span className="block font-display text-2xl tabular-nums">{ratio(gap.ratio)}</span>
          <span className="block text-sm tabular-nums text-muted">
            {formatMarketValue(gap.market_eur)} → {formatMarketValue(gap.estimate_eur)}
          </span>
        </span>
      </Link>
    </li>
  );
}

export default async function UndervaluedPage(props: PageProps<"/infravalorados">) {
  const searchParams = await props.searchParams;
  const position = POSITIONS.includes(param(searchParams.pos)) ? param(searchParams.pos) : "";
  const gaps = await getValueGaps({ position: position || undefined, limit: 30 }).catch((): ValueGap[] => []);

  return (
    <div className="flex flex-col gap-8">
      <PageHeader photo={PHOTOS.scout.src} title="Infravalorados">
        Rinden como si valieran más.
      </PageHeader>

      <p className="max-w-3xl text-sm text-muted">
        Un modelo aprende qué paga el mercado por cada cosa (liga, edad, posición, goles, asistencias,
        minutos, Europa y selección) y estima cuánto debería valer cada jugador por su última temporada.
        Aquí, los jugadores de campo de hasta 29 años que más lo superan (a los porteros no sabe medirlos y la
        edad la descuenta el mercado con razón). Es una estimación, no un precio: el modelo no ve lesiones, contratos
        ni lo que no está en los números.
      </p>

      <nav className="no-scrollbar -mx-4 flex gap-1.5 overflow-x-auto px-4 text-sm sm:mx-0 sm:px-0">
        {POSITIONS.map((entry) => (
          <Link
            key={entry || "all"}
            href={entry ? `/infravalorados?pos=${entry}` : "/infravalorados"}
            className={`shrink-0 rounded-full px-3 py-1.5 font-medium ${entry === position ? "bg-ink text-bg" : "text-muted hover:text-ink"}`}
          >
            {entry ? `${positionLabel(entry)}s` : "Todos"}
          </Link>
        ))}
      </nav>

      {gaps.length > 0 ? (
        <ol className="flex flex-col">
          {gaps.map((gap, index) => (
            <Row key={gap.player_id} gap={gap} rank={index + 1} />
          ))}
        </ol>
      ) : (
        <p className="text-sm text-muted">Las estimaciones se calculan con el próximo refresco de datos.</p>
      )}
    </div>
  );
}
