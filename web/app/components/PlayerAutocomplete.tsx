"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { Avatar } from "@/app/components/Avatar";
import { IconSearch } from "@/app/components/icons";
import { listPlayers, type PlayerSummary } from "@/lib/api";
import { positionShort } from "@/lib/format";

const DEBOUNCE_MS = 200;
const MAX_RESULTS = 8;

export function PlayerAutocomplete({
  initialPlayer = null,
  onSelect,
  placeholder,
  size = "md",
  accent = "#3d8bff",
  autoFocus = false,
}: {
  initialPlayer?: PlayerSummary | null;
  onSelect: (player: PlayerSummary | null) => void;
  placeholder: string;
  size?: "md" | "lg";
  accent?: string;
  autoFocus?: boolean;
}) {
  const [query, setQuery] = useState(initialPlayer?.name ?? "");
  const [selectedName, setSelectedName] = useState(initialPlayer?.name ?? null);
  const [results, setResults] = useState<PlayerSummary[]>([]);
  const [open, setOpen] = useState(false);
  const [highlighted, setHighlighted] = useState(0);
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
          if (!cancelled) {
            setResults(players);
            setHighlighted(0);
          }
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

  function choose(player: PlayerSummary) {
    onSelect(player);
    setSelectedName(player.name);
    setQuery(player.name);
    setOpen(false);
  }

  const large = size === "lg";

  return (
    <div className="relative w-full" ref={containerRef}>
      <div
        className={`glass flex items-center gap-3 rounded-2xl transition focus-within:border-white/25 ${large ? "px-5 py-4" : "px-4 py-2.5"}`}
        style={{ boxShadow: open ? `0 0 0 3px ${accent}33` : undefined }}
      >
        <IconSearch size={large ? 22 : 18} color={accent} />
        <input
          type="text"
          value={query}
          placeholder={placeholder}
          autoFocus={autoFocus}
          onFocus={() => setOpen(true)}
          onKeyDown={(event) => {
            if (!open || results.length === 0) return;
            if (event.key === "ArrowDown") {
              event.preventDefault();
              setHighlighted((index) => (index + 1) % results.length);
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              setHighlighted((index) => (index - 1 + results.length) % results.length);
            } else if (event.key === "Enter") {
              event.preventDefault();
              choose(results[highlighted]);
            } else if (event.key === "Escape") {
              setOpen(false);
            }
          }}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
            if (selectedName !== null) {
              setSelectedName(null);
              onSelect(null);
            }
          }}
          className={`w-full bg-transparent outline-none placeholder:text-muted ${large ? "text-lg" : "text-sm"}`}
        />
      </div>
      <AnimatePresence>
        {open && results.length > 0 && (
          <motion.ul
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full z-50 mt-2 max-h-96 w-full overflow-auto rounded-2xl border border-line bg-[#0a0f1c]/95 p-1.5 shadow-2xl backdrop-blur-xl"
          >
            {results.map((player, index) => (
              <li key={player.player_id}>
                <button
                  type="button"
                  onMouseEnter={() => setHighlighted(index)}
                  onClick={() => choose(player)}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm transition ${index === highlighted ? "bg-white/8" : ""}`}
                >
                  <Avatar name={player.name} photoUrl={player.photo_url} size={34} />
                  <span className="flex-1 truncate font-medium">{player.name}</span>
                  <span className="rounded-md bg-white/5 px-1.5 py-0.5 text-[10px] font-semibold tracking-wider text-muted">
                    {positionShort(player.position)}
                  </span>
                  {player.latest_season_year && (
                    <span className="text-xs tabular-nums text-muted">
                      {player.latest_season_year}
                    </span>
                  )}
                </button>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
