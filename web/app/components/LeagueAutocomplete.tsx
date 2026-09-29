"use client";

import { useEffect, useRef, useState } from "react";
import { searchLeagues, type LeagueSummary } from "@/lib/api";

const MIN_QUERY_LENGTH = 2;
const DEBOUNCE_MS = 300;

export function LeagueAutocomplete({
  selected,
  onSelect,
  placeholder,
}: {
  selected: LeagueSummary | null;
  onSelect: (league: LeagueSummary | null) => void;
  placeholder: string;
}) {
  const [query, setQuery] = useState(selected?.name ?? "");
  const [results, setResults] = useState<LeagueSummary[]>([]);
  const [loading, setLoading] = useState(false);
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
    const trimmed = query.trim();
    if (trimmed.length < MIN_QUERY_LENGTH || trimmed === selected?.name) {
      return;
    }
    let cancelled = false;
    const timeout = setTimeout(() => {
      if (cancelled) return;
      setLoading(true);
      searchLeagues(trimmed)
        .then((leagues) => {
          if (!cancelled) setResults(leagues);
        })
        .catch(() => {
          if (!cancelled) setResults([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, DEBOUNCE_MS);
    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [query, selected]);

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
        className="w-64 rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
      />
      {open && query.trim().length >= MIN_QUERY_LENGTH && (loading || results.length > 0) && (
        <ul className="absolute top-full z-10 mt-1 max-h-64 w-64 overflow-auto rounded-md border border-zinc-200 bg-white shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
          {loading && (
            <li className="px-3 py-2 text-xs text-zinc-500 dark:text-zinc-400">
              Buscando…
            </li>
          )}
          {!loading &&
            results.map((league) => (
              <li key={league.id}>
                <button
                  type="button"
                  onClick={() => {
                    onSelect(league);
                    setQuery(league.name);
                    setOpen(false);
                  }}
                  className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left hover:bg-zinc-100 dark:hover:bg-zinc-800"
                >
                  <span>{league.name}</span>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    {league.country}
                  </span>
                </button>
              </li>
            ))}
        </ul>
      )}
    </div>
  );
}
