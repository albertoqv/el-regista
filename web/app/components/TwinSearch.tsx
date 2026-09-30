"use client";

import { useRouter } from "next/navigation";
import { PlayerAutocomplete } from "@/app/components/PlayerAutocomplete";

export function TwinSearch({ autoFocus = false }: { autoFocus?: boolean }) {
  const router = useRouter();
  return (
    <PlayerAutocomplete
      size="lg"
      accent="#ffd76a"
      autoFocus={autoFocus}
      onSelect={(player) => {
        if (player) router.push(`/gemelos?p=${player.player_id}`);
      }}
      placeholder="¿A quién quieres fichar? Escribe su nombre…"
    />
  );
}
