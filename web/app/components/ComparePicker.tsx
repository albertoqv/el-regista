"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PlayerAutocomplete } from "@/app/components/PlayerAutocomplete";
import { getPlayerCompetitions, listPlayerSeasons, type PlayerSummary, type Season } from "@/lib/api";
import { seasonDisplay, sortSeasonsByRecency } from "@/lib/format";
import { HISTORY_PREFIX, type HistorySeasonRef } from "@/lib/history";
import { CAREER, clubSeasons } from "@/lib/seasons";

const LATEST = "";

function seasonKey(season: Season): string {
  return `${season.competition}|${season.label}`;
}

function SeasonSelect({
  playerId,
  name,
  value,
  onChange,
  color,
}: {
  playerId: number | null;
  name: string | null;
  value: string;
  onChange: (value: string) => void;
  color: string;
}) {
  const [seasons, setSeasons] = useState<Season[]>([]);
  // Whole club seasons (every competition), back to 2019: older than the league
  // seasons with detailed metrics.
  const [whole, setWhole] = useState<Season[]>([]);
  // Big five seasons from 2014 to 2023 (Understat, static files): radar included.
  const [history, setHistory] = useState<HistorySeasonRef[]>([]);

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
    getPlayerCompetitions(playerId)
      .then((lines) => {
        if (!cancelled) setWhole(clubSeasons(lines));
      })
      .catch(() => {
        if (!cancelled) setWhole([]);
      });
    if (name) {
      fetch(`/historico/temporadas?nombre=${encodeURIComponent(name)}`)
        .then((response) => (response.ok ? response.json() : []))
        .then((result: HistorySeasonRef[]) => {
          if (!cancelled) setHistory(result);
        })
        .catch(() => {
          if (!cancelled) setHistory([]);
        });
    }
    return () => {
      cancelled = true;
    };
  }, [playerId, name]);

  if (playerId === null) return null;

  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="glass w-full rounded-xl px-3 py-2 text-sm outline-none"
      style={{ borderColor: `${color}55` }}
    >
      <option value={LATEST}>Última temporada</option>
      {seasons.length > 0 && (
        <optgroup label="Liga, con métricas detalladas">
          {seasons.map((season) => (
            <option key={seasonKey(season)} value={seasonKey(season)}>
              {season.competition} {seasonDisplay(season.label)}
              {season.team ? ` · ${season.team}` : ""}
            </option>
          ))}
        </optgroup>
      )}
      {whole.length > 0 && (
        <optgroup label="Temporada completa (liga, Europa y copas)">
          {whole.map((season) => (
            <option key={seasonKey(season)} value={seasonKey(season)}>
              {seasonDisplay(season.label)}
              {season.team ? ` · ${season.team}` : ""}
            </option>
          ))}
        </optgroup>
      )}
      {history.length > 0 && (
        <optgroup label="Histórico desde 2014 (Understat, con radar)">
          {history
            // Seasons the database has in detail are listed above.
            .filter((entry) => !seasons.some((s) => s.competition === entry.competition && s.label === String(entry.year)))
            .map((season) => (
            <option
              key={`${season.competition}|${season.year}`}
              value={`${HISTORY_PREFIX}${season.competition}|${season.year}`}
            >
              {season.competition} {seasonDisplay(String(season.year))} · {season.team}
            </option>
          ))}
        </optgroup>
      )}
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
  const [nameA, setNameA] = useState<string | null>(defaultA?.name ?? null);
  const [nameB, setNameB] = useState<string | null>(defaultB?.name ?? null);
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
          accent="#2350d8"
          onSelect={(player) => {
            const id = player?.player_id ?? null;
            setPlayerA(id);
            setNameA(player?.name ?? null);
            setValueA(LATEST);
            go(id, playerB, LATEST, valueB);
          }}
          placeholder="Jugador 1…"
        />
        <SeasonSelect
          playerId={playerA}
          name={nameA}
          value={valueA}
          color="#2350d8"
          onChange={(value) => {
            setValueA(value);
            go(playerA, playerB, value, valueB);
          }}
        />
      </div>
      <span className="hidden pt-3 text-center font-heading text-sm italic text-muted md:block">
        VS
      </span>
      <div className="flex flex-col gap-2">
        <PlayerAutocomplete
          initialPlayer={defaultB}
          accent="#c93c17"
          onSelect={(player) => {
            const id = player?.player_id ?? null;
            setPlayerB(id);
            setNameB(player?.name ?? null);
            setValueB(LATEST);
            go(playerA, id, valueA, LATEST);
          }}
          placeholder="Jugador 2…"
        />
        <SeasonSelect
          playerId={playerB}
          name={nameB}
          value={valueB}
          color="#c93c17"
          onChange={(value) => {
            setValueB(value);
            go(playerA, playerB, valueA, value);
          }}
        />
      </div>
    </div>
  );
}
