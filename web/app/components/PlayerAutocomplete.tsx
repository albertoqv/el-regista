"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Avatar } from "@/app/components/Avatar";
import type { PlayerSummary } from "@/lib/api";

export function PlayerAutocomplete({
  players,
  selectedId,
  onSelect,
  placeholder,
}: {
  players: PlayerSummary[];
  selectedId: number | null;
  onSelect: (player: PlayerSummary | null) => void;
  placeholder: string;
}) {
  const selected = players.find((player) => player.player_id === selectedId) ?? null;
  const [query, setQuery] = useState(selected?.name ?? "");
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

  const matches = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const filtered =
      normalized === ""
        ? players
        : players.filter((player) =>
            player.name.toLowerCase().includes(normalized),
          );
    return filtered.slice(0, 8);
  }, [players, query]);

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
          if (selected) {
            onSelect(null);
          }
        }}
        className="w-56 rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
      />
      {open && matches.length > 0 && (
        <ul className="absolute top-full z-10 mt-1 max-h-64 w-56 overflow-auto rounded-md border border-zinc-200 bg-white shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
          {matches.map((player) => (
            <li key={player.player_id}>
              <button
                type="button"
                onClick={() => {
                  onSelect(player);
                  setQuery(player.name);
                  setOpen(false);
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-zinc-100 dark:hover:bg-zinc-800"
              >
                <Avatar name={player.name} photoUrl={player.photo_url} size={24} />
                {player.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
