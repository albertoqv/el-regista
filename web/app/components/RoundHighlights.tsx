import Link from "next/link";
import type { ComponentType } from "react";
import { IconAttack, IconCard, IconCreate, IconTarget, IconTrophy } from "@/app/components/icons";
import { kickoffDate } from "@/app/components/Forecast";
import { ScoutNote, Sticker } from "@/app/components/ScoutNote";
import type { Highlights, Pick } from "@/lib/api";

const CATEGORIES: {
  key: Pick["category"];
  title: string;
  icon: ComponentType<{ size?: number; color?: string }>;
}[] = [
  { key: "result", title: "Resultado", icon: IconTrophy },
  { key: "goals", title: "Goles", icon: IconAttack },
  { key: "corners", title: "Córners", icon: IconCreate },
  { key: "cards", title: "Tarjetas", icon: IconCard },
  { key: "scorers", title: "Goleadores", icon: IconTarget },
];

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function when(iso: string): string {
  return kickoffDate(iso).toLocaleDateString("es-ES", {
    weekday: "short",
    day: "numeric",
    timeZone: "Europe/Madrid",
  });
}

function PickRow({ pick, top }: { pick: Pick; top: boolean }) {
  return (
    <Link
      href={`/predicciones/${pick.match_id}`}
      className="group flex items-center gap-3 rounded-lg px-3 py-2.5 transition hover:bg-white/5"
    >
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-sm font-semibold">{pick.label}</span>
        <span className="flex items-center gap-1.5 truncate text-xs text-muted">
          {pick.home_team} – {pick.away_team} · {when(pick.kickoff)}
        </span>
      </span>
      <span className={`font-display text-xl font-bold tabular-nums ${top ? "text-[#9ccfea]" : ""}`}>
        {percent(pick.probability)}
      </span>
    </Link>
  );
}

/** The most likely outcomes of the next round, one column per market family. */
export function RoundHighlights({ highlights, compact = false }: { highlights: Highlights; compact?: boolean }) {
  if (highlights.picks.length === 0) return null;
  const categories = compact ? CATEGORIES.filter((c) => c.key !== "cards") : CATEGORIES;
  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <ScoutNote rotate={-2}>lo que dicen los números</ScoutNote>
          <h2 className="font-display text-3xl font-bold tracking-tight">
            Lo más probable de la jornada
          </h2>
          <p className="text-sm text-muted">
            Desde el {kickoffDate(highlights.window_start).toLocaleDateString("es-ES", { day: "numeric", month: "long" })}
          </p>
        </div>
        <Sticker tone="yellow" rotate={3}>
          Top jornada
        </Sticker>
      </div>
      <div className={`grid grid-cols-1 gap-4 sm:grid-cols-2 ${compact ? "lg:grid-cols-4" : "lg:grid-cols-5"}`}>
        {categories.map((category) => {
          const picks = highlights.picks.filter((pick) => pick.category === category.key);
          if (picks.length === 0) return null;
          return (
            <div key={category.key} className="glass flex flex-col rounded-lg p-3">
              <h3 className="flex items-center gap-2 px-3 pb-1 pt-2 font-display text-lg font-bold">
                <category.icon size={18} color="#9ccfea" />
                {category.title}
              </h3>
              {picks.slice(0, compact ? 3 : 5).map((pick, index) => (
                <PickRow key={`${pick.match_id}-${pick.label}`} pick={pick} top={index === 0} />
              ))}
            </div>
          );
        })}
      </div>
    </section>
  );
}
