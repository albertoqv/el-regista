"use client";

import { useRouter } from "next/navigation";
import { PlayerAutocomplete } from "@/app/components/PlayerAutocomplete";

export function PlayerSearchForm({
  size = "lg",
  placeholder = "Busca cualquier jugador: Yamal, Haaland, Pedri…",
}: {
  size?: "md" | "lg";
  placeholder?: string;
}) {
  const router = useRouter();

  return (
    <PlayerAutocomplete
      size={size}
      onSelect={(player) => {
        if (player) {
          router.push(`/players/${player.player_id}`);
        }
      }}
      placeholder={placeholder}
    />
  );
}
