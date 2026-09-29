"use client";

import { useEffect, useRef, useState } from "react";
import { Avatar } from "@/app/components/Avatar";
import { listPlayers, type PlayerSummary } from "@/lib/api";

const DEBOUNCE_MS = 250;
const MAX_RESULTS = 8;

export function PlayerAutocomplete({
  initialPlayer = null,
  onSelect,
  placeholder,
}: {
  initialPlayer?: PlayerSummary | null;
  onSelect: (player: PlayerSummary | null) => void;
  placeholder: string;
}) {
  const [query, setQuery] = useState(initialPlayer?.name ?? "");
  const [selectedName, setSelectedName] = useState(initialPlayer?.name ?? null);
  const [results, setResults] = useState<PlayerSummary[]>([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!open) return;
    const trimmed = query.trim();
    const searchingSelected = trimmed === selectedName;
    let cancelled = false;
    const timeout = setTimeout(() => {
      listPlayers({
        q: trimmed && !searchingSelected ? trimmed : undefined,
        sort: "recent",
        limit: MAX_RESULTS,
      })
        .then((players) => {
          if (!cancelled) setResults(players);
        })
        .catch(() => {
          if (!cancelled) setResults([]);
        });
    }, DEBOUNCE_MS);
    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [query, open, selectedName]);

  return (
    <div className="relative flex flex-col gap-1 text-sm" ref={containerRef}>
      <input
        type="text"
        value={query}
        placeholder={placeholder}
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
          if (selectedName !== null) {
            setSelectedName(null);
            onSelect(null);
          }
        }}
        className="w-64 rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
      />
      {open && results.length > 0 && (
        <ul className="absolute top-full z-10 mt-1 max-h-72 w-64 overflow-auto rounded-md border border-zinc-200 bg-white shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
          {results.map((player) => (
            <li key={player.player_id}>
              <button
                type="button"
                onClick={() => {
                  onSelect(player);
                  setSelectedName(player.name);
                  setQuery(player.name);
                  setOpen(false);
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-zinc-100 dark:hover:bg-zinc-800"
              >
                <Avatar name={player.name} photoUrl={player.photo_url} size={24} />
                <span className="flex-1 truncate">{player.name}</span>
                {player.latest_season_year && (
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    {player.latest_season_year}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
