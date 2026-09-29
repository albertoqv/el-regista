"use client";

import { useRouter } from "next/navigation";
import { PlayerAutocomplete } from "@/app/components/PlayerAutocomplete";
import type { PlayerSummary } from "@/lib/api";

export function PlayerSearchForm({ players }: { players: PlayerSummary[] }) {
  const router = useRouter();

  return (
    <PlayerAutocomplete
      players={players}
      selectedId={null}
      onSelect={(player) => {
        if (player) {
          router.push(`/players/${player.player_id}`);
        }
      }}
      placeholder="Buscar un jugador por nombre…"
    />
  );
}
