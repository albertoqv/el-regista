"use client";

import { useRouter } from "next/navigation";
import { PlayerAutocomplete } from "@/app/components/PlayerAutocomplete";

export function PlayerSearchForm({ size = "lg" }: { size?: "md" | "lg" }) {
  const router = useRouter();

  return (
    <PlayerAutocomplete
      size={size}
      onSelect={(player) => {
        if (player) {
          router.push(`/players/${player.player_id}`);
        }
      }}
      placeholder="Busca cualquier jugador: Yamal, Haaland, Pedri…"
    />
  );
}
