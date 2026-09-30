"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PlayerAutocomplete } from "@/app/components/PlayerAutocomplete";
import { listPlayerSeasons, type PlayerSummary, type Season } from "@/lib/api";
import { seasonDisplay, sortSeasonsByRecency } from "@/lib/format";
import { CAREER } from "@/lib/seasons";

const LATEST = "";

function seasonKey(season: Season): string {
  return `${season.competition}|${season.label}`;
}

function SeasonSelect({
  playerId,
  value,
  onChange,
  color,
}: {
  playerId: number | null;
  value: string;
  onChange: (value: string) => void;
  color: string;
}) {
  const [seasons, setSeasons] = useState<Season[]>([]);

  useEffect(() => {
    if (playerId === null) return;
    let cancelled = false;
    listPlayerSeasons(playerId)
      .then((result) => {
        if (!cancelled) setSeasons(sortSeasonsByRecency(result));
      })
      .catch(() => {
        if (!cancelled) setSeasons([]);
      });
    return () => {
      cancelled = true;
    };
  }, [playerId]);

  if (playerId === null) return null;

  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="glass w-full rounded-xl px-3 py-2 text-sm outline-none"
      style={{ borderColor: `${color}55` }}
    >
      <option value={LATEST}>Última temporada</option>
      {seasons.map((season) => (
        <option key={seasonKey(season)} value={seasonKey(season)}>
          {season.competition} {seasonDisplay(season.label)}
          {season.team ? ` · ${season.team}` : ""}
        </option>
      ))}
      <option value={CAREER}>Carrera completa</option>
    </select>
  );
}

function initialValue(season: Season | null, career: boolean): string {
  if (career) return CAREER;
  return season ? seasonKey(season) : LATEST;
}

function applySeason(params: URLSearchParams, value: string, prefix: "a" | "b") {
  if (value === CAREER) {
    params.set(`s${prefix}l`, CAREER);
  } else if (value !== LATEST) {
    const [competition, label] = value.split("|");
    params.set(`s${prefix}c`, competition);
    params.set(`s${prefix}l`, label);
  }
}

export function ComparePicker({
  defaultA,
  defaultB,
  seasonA,
  seasonB,
  careerA,
  careerB,
}: {
  defaultA: PlayerSummary | null;
  defaultB: PlayerSummary | null;
  seasonA: Season | null;
  seasonB: Season | null;
  careerA: boolean;
  careerB: boolean;
}) {
  const router = useRouter();
  const [playerA, setPlayerA] = useState<number | null>(defaultA?.player_id ?? null);
  const [playerB, setPlayerB] = useState<number | null>(defaultB?.player_id ?? null);
  const [valueA, setValueA] = useState(initialValue(seasonA, careerA));
  const [valueB, setValueB] = useState(initialValue(seasonB, careerB));

  function go(a: number | null, b: number | null, nextA: string, nextB: string) {
    if (a === null || b === null) return;
    const params = new URLSearchParams({ a: String(a), b: String(b) });
    applySeason(params, nextA, "a");
    applySeason(params, nextB, "b");
    router.push(`/compare?${params.toString()}`, { scroll: false });
  }

  return (
    <div className="grid grid-cols-1 items-start gap-3 md:grid-cols-[1fr_auto_1fr]">
      <div className="flex flex-col gap-2">
        <PlayerAutocomplete
          initialPlayer={defaultA}
          accent="#3d8bff"
          onSelect={(player) => {
            const id = player?.player_id ?? null;
            setPlayerA(id);
            setValueA(LATEST);
            go(id, playerB, LATEST, valueB);
          }}
          placeholder="Jugador 1…"
        />
        <SeasonSelect
          playerId={playerA}
          value={valueA}
          color="#3d8bff"
          onChange={(value) => {
            setValueA(value);
            go(playerA, playerB, value, valueB);
          }}
        />
      </div>
      <span className="hidden pt-3 text-center font-display text-sm font-bold italic text-muted md:block">
        VS
      </span>
      <div className="flex flex-col gap-2">
        <PlayerAutocomplete
          initialPlayer={defaultB}
          accent="#ff6b3d"
          onSelect={(player) => {
            const id = player?.player_id ?? null;
            setPlayerB(id);
            setValueB(LATEST);
            go(playerA, id, valueA, LATEST);
          }}
          placeholder="Jugador 2…"
        />
        <SeasonSelect
          playerId={playerB}
          value={valueB}
          color="#ff6b3d"
          onChange={(value) => {
            setValueB(value);
            go(playerA, playerB, valueA, value);
          }}
        />
      </div>
    </div>
  );
}
