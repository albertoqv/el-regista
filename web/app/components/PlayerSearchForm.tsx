"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function PlayerSearchForm() {
  const router = useRouter();
  const [playerId, setPlayerId] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (playerId.trim() !== "") {
      router.push(`/players/${playerId.trim()}`);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="number"
        inputMode="numeric"
        placeholder="ID de jugador (p. ej. 5503)"
        value={playerId}
        onChange={(event) => setPlayerId(event.target.value)}
        className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
      />
      <button
        type="submit"
        className="shrink-0 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-300"
      >
        Ver ficha
      </button>
    </form>
  );
}
