import type { Metadata } from "next";
import { Reveal } from "@/app/components/Reveal";
import { Partnerships } from "@/app/components/Partnerships";
import { PlayerSearchForm } from "@/app/components/PlayerSearchForm";
import { ScoutNote } from "@/app/components/ScoutNote";
import { SeasonLeaders } from "@/app/components/SeasonLeaders";
import { SeasonMoments } from "@/app/components/SeasonMoments";
import {
  listPartnerships,
  listSeasonLeaders,
  listShotLeaders,
  type Partnership,
  type SeasonLeader,
  type ShotLeader,
} from "@/lib/api";
import { currentSeasonStartYear } from "@/lib/format";

export const metadata: Metadata = {
  title: "Buscar jugador · El Regista",
  description: "Busca cualquier jugador y mira su ficha: radar, tiros, valor de mercado y gemelos.",
};

export default async function SearchPage() {
  const startYear = currentSeasonStartYear();
  const [scorers, moments, pairs] = await Promise.all([
    listSeasonLeaders(startYear, { metric: "goals", limit: 10 }).catch((): SeasonLeader[] => []),
    listShotLeaders(startYear, { metric: "late_goals", limit: 8 }).catch((): ShotLeader[] => []),
    listPartnerships(startYear, { limit: 6 }).catch((): Partnership[] => []),
  ]);

  return (
    <div className="flex flex-col gap-12">
      <Reveal className="flex flex-col items-center gap-4 pt-6 text-center">
        <ScoutNote rotate={-2}>cualquier jugador, 14 ligas</ScoutNote>
        <h1 className="font-display text-4xl font-bold tracking-tight sm:text-5xl">Buscar jugador</h1>
        <p className="max-w-xl text-sm text-muted sm:text-base">Ficha completa de cualquier jugador.</p>
        <div className="w-full max-w-2xl">
          <PlayerSearchForm />
        </div>
      </Reveal>
      {scorers.length > 0 ? <SeasonLeaders startYear={startYear} initialLeaders={scorers} /> : null}
      {moments.length > 0 ? <SeasonMoments startYear={startYear} initialLeaders={moments} /> : null}
      <Partnerships pairs={pairs} />
    </div>
  );
}
