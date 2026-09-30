"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PlayerAutocomplete } from "@/app/components/PlayerAutocomplete";
import { listPlayerSeasons, type PlayerSummary, type Season } from "@/lib/api";

function seasonKey(season: Season): string {
  return `${season.competition}|${season.label}`;
}

function SeasonSelect({
  playerId,
  value,
  onChange,
}: {
  playerId: number | null;
  value: Season | null;
  onChange: (season: Season | null) => void;
}) {
  const [seasons, setSeasons] = useState<Season[]>([]);

  useEffect(() => {
    if (playerId === null) {
      return;
    }
    let cancelled = false;
    listPlayerSeasons(playerId)
      .then((result) => {
        if (!cancelled) setSeasons(result);
      })
      .catch(() => {
        if (!cancelled) setSeasons([]);
      });
    return () => {
      cancelled = true;
    };
  }, [playerId]);

  if (playerId === null || seasons.length === 0) {
    return null;
  }

  return (
    <select
      value={value ? seasonKey(value) : ""}
      onChange={(event) => {
        if (event.target.value === "") {
          onChange(null);
          return;
        }
        const [competition, label] = event.target.value.split("|");
        onChange({ competition, label });
      }}
      className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
    >
      <option value="">Carrera</option>
      {seasons.map((season) => (
        <option key={seasonKey(season)} value={seasonKey(season)}>
          {season.competition} {season.label}
          {season.team ? ` · ${season.team}` : ""}
        </option>
      ))}
    </select>
  );
}

export function ComparePicker({
  defaultA,
  defaultB,
  defaultSeasonA,
  defaultSeasonB,
}: {
  defaultA: PlayerSummary | null;
  defaultB: PlayerSummary | null;
  defaultSeasonA: Season | null;
  defaultSeasonB: Season | null;
}) {
  const router = useRouter();
  const [playerA, setPlayerA] = useState<number | null>(
    defaultA?.player_id ?? null,
  );
  const [playerB, setPlayerB] = useState<number | null>(
    defaultB?.player_id ?? null,
  );
  const [seasonA, setSeasonA] = useState<Season | null>(defaultSeasonA);
  const [seasonB, setSeasonB] = useState<Season | null>(defaultSeasonB);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (playerA === null || playerB === null) return;
    const params = new URLSearchParams({ a: String(playerA), b: String(playerB) });
    if (seasonA) {
      params.set("sac", seasonA.competition);
      params.set("sal", seasonA.label);
    }
    if (seasonB) {
      params.set("sbc", seasonB.competition);
      params.set("sbl", seasonB.label);
    }
    router.push(`/compare?${params.toString()}`);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
      <div className="flex flex-col gap-2">
        <PlayerAutocomplete
          initialPlayer={defaultA}
          onSelect={(player) => {
            setPlayerA(player?.player_id ?? null);
            setSeasonA(null);
          }}
          placeholder="Buscar jugador A…"
        />
        <SeasonSelect playerId={playerA} value={seasonA} onChange={setSeasonA} />
      </div>
      <span className="pb-2 text-sm text-zinc-500 dark:text-zinc-400">vs</span>
      <div className="flex flex-col gap-2">
        <PlayerAutocomplete
          initialPlayer={defaultB}
          onSelect={(player) => {
            setPlayerB(player?.player_id ?? null);
            setSeasonB(null);
          }}
          placeholder="Buscar jugador B…"
        />
        <SeasonSelect playerId={playerB} value={seasonB} onChange={setSeasonB} />
      </div>
      <button
        type="submit"
        disabled={playerA === null || playerB === null}
        className="rounded-md bg-[#2a78d6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1f5da8] disabled:opacity-50"
      >
        Comparar
      </button>
    </form>
  );
}
