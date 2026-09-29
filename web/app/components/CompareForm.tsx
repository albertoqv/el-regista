"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function CompareForm({
  defaultA = "",
  defaultB = "",
}: {
  defaultA?: string;
  defaultB?: string;
}) {
  const router = useRouter();
  const [playerIdA, setPlayerIdA] = useState(defaultA);
  const [playerIdB, setPlayerIdB] = useState(defaultB);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (playerIdA.trim() !== "" && playerIdB.trim() !== "") {
      router.push(`/compare?a=${playerIdA.trim()}&b=${playerIdB.trim()}`);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
      <label className="flex flex-col gap-1 text-sm">
        Jugador A
        <input
          type="number"
          inputMode="numeric"
          value={playerIdA}
          onChange={(event) => setPlayerIdA(event.target.value)}
          className="rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Jugador B
        <input
          type="number"
          inputMode="numeric"
          value={playerIdB}
          onChange={(event) => setPlayerIdB(event.target.value)}
          className="rounded-md border border-zinc-300 bg-white px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
        />
      </label>
      <button
        type="submit"
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-300"
      >
        Comparar
      </button>
    </form>
  );
}
