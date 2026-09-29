"use client";

import { useRouter } from "next/navigation";
import { PlayerAutocomplete } from "@/app/components/PlayerAutocomplete";

export function PlayerSearchForm() {
  const router = useRouter();

  return (
    <PlayerAutocomplete
      onSelect={(player) => {
        if (player) {
          router.push(`/players/${player.player_id}`);
        }
      }}
      placeholder="Buscar un jugador por nombre…"
    />
  );
}
