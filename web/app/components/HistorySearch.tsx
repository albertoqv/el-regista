"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { IconSearch } from "@/app/components/icons";
import { seasonDisplay } from "@/lib/format";

type Result = { id: number; name: string; team: string; first: number; last: number; seasons: number };

const DEBOUNCE_MS = 200;

/** Any player of the big five since 2014, by name (static history, no database). */
export function HistorySearch({ placeholder }: { placeholder: string }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Result[]>([]);

  useEffect(() => {
    const trimmed = query.trim();
    let cancelled = false;
    const timeout = setTimeout(() => {
      if (trimmed.length < 2) {
        setResults([]);
        return;
      }
      fetch(`/historico/buscar?q=${encodeURIComponent(trimmed)}`)
        .then((response) => (response.ok ? response.json() : []))
        .then((found: Result[]) => {
          if (!cancelled) setResults(found);
        })
        .catch(() => {
          if (!cancelled) setResults([]);
        });
    }, DEBOUNCE_MS);
    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [query]);

  return (
    <div className="on-paper w-full">
      <label className="glass flex items-center gap-3 rounded-lg px-5 py-4 focus-within:border-ink/25">
        <IconSearch size={22} color="#c93c17" />
        <input
          type="text"
          value={query}
          placeholder={placeholder}
          onChange={(event) => setQuery(event.target.value)}
          className="w-full bg-transparent text-lg outline-none placeholder:text-muted"
        />
      </label>
      {results.length > 0 && (
        <ul className="glass mt-2 divide-y divide-line rounded-lg">
          {results.map((result) => (
            <li key={result.id}>
              <Link href={`/epocas?j=${result.id}`} className="flex items-baseline justify-between gap-4 px-5 py-3 hover:bg-ink/5">
                <span className="font-semibold">{result.name}</span>
                <span className="text-right text-sm text-muted">
                  {result.team} · {seasonDisplay(String(result.first))}
                  {result.last !== result.first ? ` a ${seasonDisplay(String(result.last))}` : ""}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
